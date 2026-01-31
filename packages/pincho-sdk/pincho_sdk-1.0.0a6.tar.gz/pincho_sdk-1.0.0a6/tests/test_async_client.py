"""Tests for asynchronous Pincho client."""

import httpx
import pytest
from pytest_httpx import HTTPXMock

from pincho import AsyncPincho
from pincho.exceptions import (
    AuthenticationError,
    PinchoError,
    ValidationError,
)


class TestAsyncPincho:
    """Test suite for AsyncPincho asynchronous client."""

    def test_init(self) -> None:
        """Test client initialization with token."""
        client = AsyncPincho(token="abc12345")
        assert client.token == "abc12345"
        assert client.timeout == 30.0
        assert client.base_url == AsyncPincho.BASE_URL

    def test_init_missing_token_raises_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that missing token raises ValueError."""
        # Ensure no env var is set
        monkeypatch.delenv("PINCHO_TOKEN", raising=False)
        with pytest.raises(ValueError, match="Token is required"):
            AsyncPincho()

    def test_init_empty_token_raises_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that empty token raises ValueError."""
        monkeypatch.delenv("PINCHO_TOKEN", raising=False)
        with pytest.raises(ValueError, match="Token is required"):
            AsyncPincho(token="")

    def test_init_from_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test client initialization from PINCHO_TOKEN env var."""
        monkeypatch.setenv("PINCHO_TOKEN", "env_token_123")
        client = AsyncPincho()
        assert client.token == "env_token_123"

    def test_init_timeout_from_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test timeout initialization from PINCHO_TIMEOUT env var."""
        monkeypatch.setenv("PINCHO_TIMEOUT", "60.0")
        client = AsyncPincho(token="abc12345")
        assert client.timeout == 60.0

    def test_init_max_retries_from_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test max_retries initialization from PINCHO_MAX_RETRIES env var."""
        monkeypatch.setenv("PINCHO_MAX_RETRIES", "5")
        client = AsyncPincho(token="abc12345")
        assert client.max_retries == 5

    def test_init_explicit_overrides_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that explicit parameters override environment variables."""
        monkeypatch.setenv("PINCHO_TOKEN", "env_token")
        monkeypatch.setenv("PINCHO_TIMEOUT", "60.0")
        monkeypatch.setenv("PINCHO_MAX_RETRIES", "5")
        client = AsyncPincho(token="explicit_token", timeout=10.0, max_retries=1)
        assert client.token == "explicit_token"
        assert client.timeout == 10.0
        assert client.max_retries == 1

    def test_init_custom_timeout(self) -> None:
        """Test client initialization with custom timeout."""
        client = AsyncPincho(token="abc12345", timeout=60.0)
        assert client.timeout == 60.0

    def test_init_custom_base_url(self) -> None:
        """Test client initialization with custom base URL."""
        client = AsyncPincho(
            token="abc12345",
            base_url="https://custom.example.com",
        )
        assert client.base_url == "https://custom.example.com"

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Test client as async context manager."""
        async with AsyncPincho(token="abc12345") as client:
            assert client.token == "abc12345"
        # Client should be closed after exiting context

    @pytest.mark.asyncio
    async def test_send_success(self, httpx_mock: HTTPXMock) -> None:
        """Test successful notification send."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/send",
            json={"status": "success", "message": "Notification sent successfully"},
            status_code=200,
        )

        async with AsyncPincho(token="abc12345") as client:
            response = await client.send("Test Title", "Test message")
            assert response.status == "success"
            assert response.message == "Notification sent successfully"

    @pytest.mark.asyncio
    async def test_send_with_all_parameters(self, httpx_mock: HTTPXMock) -> None:
        """Test send with all optional parameters."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/send",
            json={"status": "success", "message": "Notification sent"},
            status_code=200,
        )

        async with AsyncPincho(token="abc12345") as client:
            response = await client.send(
                "Test Title",
                "Test message",
                type="alert",
                tags=["urgent", "production"],
                image_url="https://example.com/image.png",
                action_url="https://example.com/action",
            )
            assert response.status == "success"

        # Verify request payload and headers
        request = httpx_mock.get_request()
        assert request is not None
        assert request.method == "POST"
        assert request.headers["Content-Type"] == "application/json"
        assert request.headers["Authorization"] == "Bearer abc12345"

        # Verify token is NOT in request body
        import json

        body = json.loads(request.content.decode())
        assert "token" not in body

    @pytest.mark.asyncio
    async def test_send_authentication_error_401(self, httpx_mock: HTTPXMock) -> None:
        """Test 401 authentication error with nested error format."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/send",
            json={
                "status": "error",
                "error": {
                    "type": "authentication_error",
                    "code": "invalid_token",
                    "message": "Invalid token",
                },
            },
            status_code=401,
        )

        async with AsyncPincho(token="abc12345") as client:
            with pytest.raises(AuthenticationError) as exc_info:
                await client.send("Test Title", "Test message")
            assert "Invalid token" in str(exc_info.value)
            assert "[invalid_token]" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_validation_error_400(self, httpx_mock: HTTPXMock) -> None:
        """Test 400 validation error with nested error format."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/send",
            json={
                "status": "error",
                "error": {
                    "type": "validation_error",
                    "code": "missing_required_field",
                    "message": "Title is required",
                    "param": "title",
                },
            },
            status_code=400,
        )

        async with AsyncPincho(token="abc12345") as client:
            with pytest.raises(ValidationError) as exc_info:
                await client.send("", "Test message")
            assert "Invalid parameters" in str(exc_info.value)
            assert "Title is required" in str(exc_info.value)
            assert "(parameter: title)" in str(exc_info.value)
            assert "[missing_required_field]" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_forbidden_error_403(self, httpx_mock: HTTPXMock) -> None:
        """Test 403 forbidden error with nested error format."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/send",
            json={
                "status": "error",
                "error": {
                    "type": "authentication_error",
                    "code": "account_disabled",
                    "message": "Account disabled",
                },
            },
            status_code=403,
        )

        async with AsyncPincho(token="abc12345") as client:
            with pytest.raises(AuthenticationError) as exc_info:
                await client.send("Test Title", "Test message")
            assert "Forbidden" in str(exc_info.value)
            assert "[account_disabled]" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_not_found_error_404(self, httpx_mock: HTTPXMock) -> None:
        """Test 404 not found error with nested error format."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/send",
            json={
                "status": "error",
                "error": {
                    "type": "validation_error",
                    "code": "not_found",
                    "message": "User not found",
                },
            },
            status_code=404,
        )

        async with AsyncPincho(token="abc12345") as client:
            with pytest.raises(ValidationError) as exc_info:
                await client.send("Test Title", "Test message")
            assert "User not found" in str(exc_info.value)
            assert "[not_found]" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_server_error_500(self, httpx_mock: HTTPXMock) -> None:
        """Test 500 server error with nested error format."""
        # Server error is retryable, so mock will be called 4 times (initial + 3 retries)
        for _ in range(4):
            httpx_mock.add_response(
                method="POST",
                url="https://api.pincho.app/send",
                json={
                    "status": "error",
                    "error": {
                        "type": "server_error",
                        "code": "internal_error",
                        "message": "Internal server error",
                    },
                },
                status_code=500,
            )

        async with AsyncPincho(token="abc12345") as client:
            with pytest.raises(PinchoError) as exc_info:
                await client.send("Test Title", "Test message")
            assert "Server error (500)" in str(exc_info.value)
            assert "[internal_error]" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_network_error(self, httpx_mock: HTTPXMock) -> None:
        """Test network error handling."""
        # Network error is retryable, so mock will be called 4 times (initial + 3 retries)
        for _ in range(4):
            httpx_mock.add_exception(httpx.ConnectError("Connection failed"))

        async with AsyncPincho(token="abc12345") as client:
            with pytest.raises(PinchoError) as exc_info:
                await client.send("Test Title", "Test message")
            assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_timeout_error(self, httpx_mock: HTTPXMock) -> None:
        """Test timeout error handling."""
        # Timeout is retryable, so mock will be called 4 times (initial + 3 retries)
        for _ in range(4):
            httpx_mock.add_exception(httpx.TimeoutException("Request timed out"))

        async with AsyncPincho(token="abc12345", timeout=1.0) as client:
            with pytest.raises(PinchoError) as exc_info:
                await client.send("Test Title", "Test message")
            assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_malformed_json_response(self, httpx_mock: HTTPXMock) -> None:
        """Test handling of malformed JSON response."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/send",
            content=b"not json",
            status_code=200,
        )

        async with AsyncPincho(token="abc12345") as client:
            with pytest.raises(PinchoError) as exc_info:
                await client.send("Test Title", "Test message")
            assert "Unexpected error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_missing_response_fields(self, httpx_mock: HTTPXMock) -> None:
        """Test handling of response with missing fields."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/send",
            json={},
            status_code=200,
        )

        async with AsyncPincho(token="abc12345") as client:
            response = await client.send("Test Title", "Test message")
            assert response.status == "unknown"
            assert response.message == ""

    @pytest.mark.asyncio
    async def test_multiple_concurrent_sends(self, httpx_mock: HTTPXMock) -> None:
        """Test multiple concurrent sends (async benefit)."""
        import asyncio

        # Mock response for all requests (add multiple times for concurrent sends)
        for _ in range(3):
            httpx_mock.add_response(
                method="POST",
                url="https://api.pincho.app/send",
                json={"status": "success", "message": "Notification sent"},
                status_code=200,
            )

        async with AsyncPincho(token="abc12345") as client:
            # Send 3 notifications concurrently
            tasks = [client.send(f"Title {i}", f"Message {i}") for i in range(3)]
            responses = await asyncio.gather(*tasks)

            # All should succeed
            assert len(responses) == 3
            for response in responses:
                assert response.status == "success"

    @pytest.mark.asyncio
    async def test_notifai_success(self, httpx_mock: HTTPXMock) -> None:
        """Test successful NotifAI notification generation."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/notifai",
            json={
                "status": "success",
                "message": "Notification generated and sent successfully",
                "notification": {
                    "title": "Deploy Complete - v2.1.3",
                    "message": "Your deployment to production has finished successfully",
                    "type": "deployment",
                    "tags": ["production", "deploy"],
                },
            },
            status_code=200,
        )

        async with AsyncPincho(token="abc12345") as client:
            response = await client.notifai(
                "deployment finished successfully, v2.1.3 is live on prod"
            )
            assert response.status == "success"
            assert response.notification is not None
            assert "title" in response.notification

        # Verify Authorization header is sent
        request = httpx_mock.get_request()
        assert request is not None
        assert request.method == "POST"
        assert request.headers["Authorization"] == "Bearer abc12345"

        # Verify token is NOT in request body
        import json

        body = json.loads(request.content.decode())
        assert "token" not in body

    @pytest.mark.asyncio
    async def test_user_agent_header_sent(self, httpx_mock: HTTPXMock) -> None:
        """Test that User-Agent header is sent with requests."""
        from pincho import __version__

        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/send",
            json={"status": "success", "message": "Notification sent"},
            status_code=200,
        )

        async with AsyncPincho(token="abc12345") as client:
            await client.send("Test Title", "Test message")

        # Verify User-Agent header is sent
        request = httpx_mock.get_request()
        assert request is not None
        assert request.headers["User-Agent"] == f"pincho-python/{__version__}"

    @pytest.mark.asyncio
    async def test_rate_limit_headers_parsed(self, httpx_mock: HTTPXMock) -> None:
        """Test that rate limit headers are parsed from response."""
        import time

        reset_time = int(time.time()) + 3600  # 1 hour from now

        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/send",
            json={"status": "success", "message": "Notification sent"},
            status_code=200,
            headers={
                "RateLimit-Limit": "100",
                "RateLimit-Remaining": "95",
                "RateLimit-Reset": str(reset_time),
            },
        )

        async with AsyncPincho(token="abc12345") as client:
            await client.send("Test Title", "Test message")

            # Verify rate limit info is stored
            assert client.last_rate_limit is not None
            assert client.last_rate_limit.limit == 100
            assert client.last_rate_limit.remaining == 95
            assert int(client.last_rate_limit.reset.timestamp()) == reset_time

    @pytest.mark.asyncio
    async def test_rate_limit_headers_missing(self, httpx_mock: HTTPXMock) -> None:
        """Test that missing rate limit headers result in None."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/send",
            json={"status": "success", "message": "Notification sent"},
            status_code=200,
        )

        async with AsyncPincho(token="abc12345") as client:
            await client.send("Test Title", "Test message")

            # Verify rate limit info is None when headers are missing
            assert client.last_rate_limit is None

    @pytest.mark.asyncio
    async def test_rate_limit_headers_partial(self, httpx_mock: HTTPXMock) -> None:
        """Test that partial rate limit headers result in None."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/send",
            json={"status": "success", "message": "Notification sent"},
            status_code=200,
            headers={
                "RateLimit-Limit": "100",
                # Missing RateLimit-Remaining and RateLimit-Reset
            },
        )

        async with AsyncPincho(token="abc12345") as client:
            await client.send("Test Title", "Test message")

            # Verify rate limit info is None when headers are incomplete
            assert client.last_rate_limit is None

    @pytest.mark.asyncio
    async def test_rate_limit_headers_on_error(self, httpx_mock: HTTPXMock) -> None:
        """Test that rate limit headers are parsed even on error responses."""
        import time

        reset_time = int(time.time()) + 3600

        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/send",
            json={
                "status": "error",
                "error": {
                    "type": "validation_error",
                    "code": "missing_required_field",
                    "message": "Title is required",
                },
            },
            status_code=400,
            headers={
                "RateLimit-Limit": "100",
                "RateLimit-Remaining": "99",
                "RateLimit-Reset": str(reset_time),
            },
        )

        async with AsyncPincho(token="abc12345") as client:
            with pytest.raises(ValidationError):
                await client.send("", "Test message")

            # Rate limit info should still be parsed on error
            assert client.last_rate_limit is not None
            assert client.last_rate_limit.limit == 100
            assert client.last_rate_limit.remaining == 99

    @pytest.mark.asyncio
    async def test_retry_after_header_used(self, httpx_mock: HTTPXMock) -> None:
        """Test that Retry-After header is used for backoff on 429."""
        # First request: 429 with Retry-After
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/send",
            json={
                "status": "error",
                "error": {
                    "type": "rate_limit_error",
                    "code": "too_many_requests",
                    "message": "Rate limit exceeded",
                },
            },
            status_code=429,
            headers={"Retry-After": "0.1"},  # Use short delay for test
        )
        # Second request: success
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/send",
            json={"status": "success", "message": "Notification sent"},
            status_code=200,
        )

        async with AsyncPincho(token="abc12345", max_retries=1) as client:
            import time

            start_time = time.time()
            response = await client.send("Test Title", "Test message")
            elapsed = time.time() - start_time

            assert response.status == "success"
            # Should have waited at least 0.1 seconds (from Retry-After)
            # but less than 5 seconds (which would be the default rate limit backoff)
            assert 0.1 <= elapsed < 5.0

    @pytest.mark.asyncio
    async def test_retry_after_header_invalid_uses_calculated(self, httpx_mock: HTTPXMock) -> None:
        """Test that invalid Retry-After header falls back to calculated backoff."""
        # First request: 429 with invalid Retry-After
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/send",
            json={
                "status": "error",
                "error": {
                    "type": "rate_limit_error",
                    "code": "too_many_requests",
                    "message": "Rate limit exceeded",
                },
            },
            status_code=429,
            headers={"Retry-After": "invalid"},  # Invalid value
        )
        # Second request: success
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/send",
            json={"status": "success", "message": "Notification sent"},
            status_code=200,
        )

        async with AsyncPincho(token="abc12345", max_retries=1) as client:
            response = await client.send("Test Title", "Test message")
            # Should still succeed with calculated backoff
            assert response.status == "success"

    @pytest.mark.asyncio
    async def test_notifai_parses_rate_limit_headers(self, httpx_mock: HTTPXMock) -> None:
        """Test that NotifAI endpoint also parses rate limit headers."""
        import time

        reset_time = int(time.time()) + 3600

        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/notifai",
            json={
                "status": "success",
                "message": "Notification generated",
                "notification": {"title": "Test"},
            },
            status_code=200,
            headers={
                "RateLimit-Limit": "50",
                "RateLimit-Remaining": "45",
                "RateLimit-Reset": str(reset_time),
            },
        )

        async with AsyncPincho(token="abc12345") as client:
            await client.notifai("test text")

            # Verify rate limit info is stored
            assert client.last_rate_limit is not None
            assert client.last_rate_limit.limit == 50
            assert client.last_rate_limit.remaining == 45

    @pytest.mark.asyncio
    async def test_notifai_retry_with_retry_after_header(self, httpx_mock: HTTPXMock) -> None:
        """Test that NotifAI retries with Retry-After header on 429."""
        # First request: 429 with Retry-After
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/notifai",
            json={
                "status": "error",
                "error": {
                    "type": "rate_limit_error",
                    "code": "too_many_requests",
                    "message": "Rate limit exceeded",
                },
            },
            status_code=429,
            headers={"Retry-After": "0.1"},
        )
        # Second request: success
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/notifai",
            json={
                "status": "success",
                "message": "Notification generated",
                "notification": {"title": "AI Generated"},
            },
            status_code=200,
        )

        async with AsyncPincho(token="abc12345", max_retries=1) as client:
            response = await client.notifai("test text")
            assert response.status == "success"
            assert response.notification is not None

    @pytest.mark.asyncio
    async def test_notifai_retry_with_invalid_retry_after(self, httpx_mock: HTTPXMock) -> None:
        """Test that NotifAI falls back to calculated backoff with invalid Retry-After."""
        # First request: 429 with invalid Retry-After
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/notifai",
            json={
                "status": "error",
                "error": {
                    "type": "rate_limit_error",
                    "code": "too_many_requests",
                    "message": "Rate limit exceeded",
                },
            },
            status_code=429,
            headers={"Retry-After": "invalid"},
        )
        # Second request: success
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/notifai",
            json={
                "status": "success",
                "message": "Notification generated",
                "notification": {"title": "AI Generated"},
            },
            status_code=200,
        )

        async with AsyncPincho(token="abc12345", max_retries=1) as client:
            response = await client.notifai("test text")
            assert response.status == "success"

    @pytest.mark.asyncio
    async def test_notifai_retries_server_error(self, httpx_mock: HTTPXMock) -> None:
        """Test that NotifAI retries on server errors (5xx)."""
        # First request: 500 server error
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/notifai",
            json={
                "status": "error",
                "error": {
                    "type": "server_error",
                    "code": "internal_error",
                    "message": "Internal server error",
                },
            },
            status_code=500,
        )
        # Second request: success
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/notifai",
            json={
                "status": "success",
                "message": "Notification generated",
                "notification": {"title": "AI Generated"},
            },
            status_code=200,
        )

        async with AsyncPincho(token="abc12345", max_retries=1) as client:
            response = await client.notifai("test text")
            assert response.status == "success"

    @pytest.mark.asyncio
    async def test_notifai_retries_network_error(self, httpx_mock: HTTPXMock) -> None:
        """Test that NotifAI retries on network errors."""
        # First request: network error
        httpx_mock.add_exception(httpx.ConnectError("Connection refused"))
        # Second request: success
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/notifai",
            json={
                "status": "success",
                "message": "Notification generated",
                "notification": {"title": "AI Generated"},
            },
            status_code=200,
        )

        async with AsyncPincho(token="abc12345", max_retries=1) as client:
            response = await client.notifai("test text")
            assert response.status == "success"

    @pytest.mark.asyncio
    async def test_http_error_with_non_json_response(self, httpx_mock: HTTPXMock) -> None:
        """Test that HTTP errors with non-JSON responses fall back to raw text."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/send",
            content=b"Internal Server Error",  # Not JSON
            status_code=500,
        )

        async with AsyncPincho(token="abc12345", max_retries=0) as client:
            from pincho.exceptions import ServerError

            with pytest.raises(ServerError) as exc_info:
                await client.send("Test", "Message")
            # Error message should contain raw response text
            assert "Internal Server Error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_notifai_non_retryable_error_not_retried(self, httpx_mock: HTTPXMock) -> None:
        """Test that NotifAI does not retry non-retryable errors."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/notifai",
            json={
                "status": "error",
                "error": {
                    "type": "validation_error",
                    "code": "text_too_short",
                    "message": "Text is too short",
                },
            },
            status_code=400,
        )

        async with AsyncPincho(token="abc12345", max_retries=3) as client:
            with pytest.raises(ValidationError):
                await client.notifai("hi")  # Too short

            # Should only have one request (no retries)
            requests = httpx_mock.get_requests()
            assert len(requests) == 1

    @pytest.mark.asyncio
    async def test_notifai_exhausts_retries(self, httpx_mock: HTTPXMock) -> None:
        """Test that NotifAI raises error after exhausting retries."""
        from pincho.exceptions import ServerError

        # All requests fail with server error
        for _ in range(3):  # max_retries + 1
            httpx_mock.add_response(
                method="POST",
                url="https://api.pincho.app/notifai",
                json={
                    "status": "error",
                    "error": {
                        "type": "server_error",
                        "code": "internal_error",
                        "message": "Server unavailable",
                    },
                },
                status_code=500,
            )

        async with AsyncPincho(token="abc12345", max_retries=2) as client:
            with pytest.raises(ServerError):
                await client.notifai("test text")

            # Should have made 3 attempts (initial + 2 retries)
            requests = httpx_mock.get_requests()
            assert len(requests) == 3
