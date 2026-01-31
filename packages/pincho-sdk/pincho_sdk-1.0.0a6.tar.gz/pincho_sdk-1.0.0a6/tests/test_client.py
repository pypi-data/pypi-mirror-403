"""Tests for synchronous Pincho client."""

import httpx
import pytest
from pytest_httpx import HTTPXMock

from pincho import Pincho
from pincho.exceptions import (
    AuthenticationError,
    PinchoError,
    ValidationError,
)


class TestPincho:
    """Test suite for Pincho synchronous client."""

    def test_init(self) -> None:
        """Test client initialization with token."""
        client = Pincho(token="abc12345")
        assert client._async_client.token == "abc12345"
        assert client._async_client.timeout == 30.0
        assert client._async_client.base_url == "https://api.pincho.app"
        client.close()

    def test_init_missing_token_raises_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that missing token raises ValueError."""
        # Clear env var to ensure test works in CI where PINCHO_TOKEN is set
        monkeypatch.delenv("PINCHO_TOKEN", raising=False)
        with pytest.raises(ValueError, match="Token is required"):
            Pincho(token="")

    def test_init_custom_timeout(self) -> None:
        """Test client initialization with custom timeout."""
        client = Pincho(token="abc12345", timeout=60.0)
        assert client._async_client.timeout == 60.0
        client.close()

    def test_init_custom_base_url(self) -> None:
        """Test client initialization with custom base URL."""
        client = Pincho(
            token="abc12345",
            base_url="https://custom.example.com",
        )
        assert client._async_client.base_url == "https://custom.example.com"
        client.close()

    def test_context_manager(self) -> None:
        """Test client as context manager."""
        with Pincho(token="abc12345") as client:
            assert client._async_client.token == "abc12345"
        # Client should be closed after exiting context

    def test_send_success(self, httpx_mock: HTTPXMock) -> None:
        """Test successful notification send."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/send",
            json={"status": "success", "message": "Notification sent successfully"},
            status_code=200,
        )

        with Pincho(token="abc12345") as client:
            response = client.send("Test Title", "Test message")
            assert response.status == "success"
            assert response.message == "Notification sent successfully"

    def test_send_with_all_parameters(self, httpx_mock: HTTPXMock) -> None:
        """Test send with all optional parameters."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/send",
            json={"status": "success", "message": "Notification sent"},
            status_code=200,
        )

        with Pincho(token="abc12345") as client:
            response = client.send(
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

    def test_send_authentication_error_401(self, httpx_mock: HTTPXMock) -> None:
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

        with Pincho(token="abc12345") as client:
            with pytest.raises(AuthenticationError) as exc_info:
                client.send("Test Title", "Test message")
            assert "Invalid token" in str(exc_info.value)
            assert "[invalid_token]" in str(exc_info.value)

    def test_send_validation_error_400(self, httpx_mock: HTTPXMock) -> None:
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

        with Pincho(token="abc12345") as client:
            with pytest.raises(ValidationError) as exc_info:
                client.send("", "Test message")
            assert "Invalid parameters" in str(exc_info.value)
            assert "Title is required" in str(exc_info.value)
            assert "(parameter: title)" in str(exc_info.value)
            assert "[missing_required_field]" in str(exc_info.value)

    def test_send_forbidden_error_403(self, httpx_mock: HTTPXMock) -> None:
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

        with Pincho(token="abc12345") as client:
            with pytest.raises(AuthenticationError) as exc_info:
                client.send("Test Title", "Test message")
            assert "Forbidden" in str(exc_info.value)
            assert "[account_disabled]" in str(exc_info.value)

    def test_send_not_found_error_404(self, httpx_mock: HTTPXMock) -> None:
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

        with Pincho(token="abc12345") as client:
            with pytest.raises(ValidationError) as exc_info:
                client.send("Test Title", "Test message")
            assert "User not found" in str(exc_info.value)
            assert "[not_found]" in str(exc_info.value)

    def test_send_server_error_500(self, httpx_mock: HTTPXMock) -> None:
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

        with Pincho(token="abc12345") as client:
            with pytest.raises(PinchoError) as exc_info:
                client.send("Test Title", "Test message")
            assert "Server error (500)" in str(exc_info.value)
            assert "[internal_error]" in str(exc_info.value)

    def test_send_network_error(self, httpx_mock: HTTPXMock) -> None:
        """Test network error handling."""
        # Network error is retryable, so mock will be called 4 times (initial + 3 retries)
        for _ in range(4):
            httpx_mock.add_exception(httpx.ConnectError("Connection failed"))

        with Pincho(token="abc12345") as client:
            with pytest.raises(PinchoError) as exc_info:
                client.send("Test Title", "Test message")
            assert "Network error" in str(exc_info.value)

    def test_send_timeout_error(self, httpx_mock: HTTPXMock) -> None:
        """Test timeout error handling."""
        # Timeout is retryable, so mock will be called 4 times (initial + 3 retries)
        for _ in range(4):
            httpx_mock.add_exception(httpx.TimeoutException("Request timed out"))

        with Pincho(token="abc12345", timeout=1.0) as client:
            with pytest.raises(PinchoError) as exc_info:
                client.send("Test Title", "Test message")
            assert "Network error" in str(exc_info.value)

    def test_send_malformed_json_response(self, httpx_mock: HTTPXMock) -> None:
        """Test handling of malformed JSON response."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/send",
            content=b"not json",
            status_code=200,
        )

        with Pincho(token="abc12345") as client:
            with pytest.raises(PinchoError) as exc_info:
                client.send("Test Title", "Test message")
            assert "Unexpected error" in str(exc_info.value)

    def test_send_missing_response_fields(self, httpx_mock: HTTPXMock) -> None:
        """Test handling of response with missing fields."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/send",
            json={},
            status_code=200,
        )

        with Pincho(token="abc12345") as client:
            response = client.send("Test Title", "Test message")
            assert response.status == "unknown"
            assert response.message == ""

    def test_last_rate_limit_property(self, httpx_mock: HTTPXMock) -> None:
        """Test that sync client exposes last_rate_limit property."""
        import time

        reset_time = int(time.time()) + 3600

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

        with Pincho(token="abc12345") as client:
            client.send("Test", "Message")

            # Access rate limit info through sync wrapper
            rate_limit = client.last_rate_limit
            assert rate_limit is not None
            assert rate_limit.limit == 100
            assert rate_limit.remaining == 95

    def test_notifai_success(self, httpx_mock: HTTPXMock) -> None:
        """Test successful NotifAI call through sync client."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/notifai",
            json={
                "status": "success",
                "message": "Notification generated",
                "notification": {
                    "title": "Deployment Complete",
                    "message": "Version 2.1.3 deployed",
                    "type": "deployment",
                },
            },
            status_code=200,
        )

        with Pincho(token="abc12345") as client:
            response = client.notifai("deployment finished, v2.1.3 is live")
            assert response.status == "success"
            assert response.notification is not None
            assert response.notification.get("title") == "Deployment Complete"

    def test_notifai_validation_error(self, httpx_mock: HTTPXMock) -> None:
        """Test NotifAI validation error through sync client."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.pincho.app/notifai",
            json={
                "status": "error",
                "error": {
                    "type": "validation_error",
                    "code": "text_too_short",
                    "message": "Text must be at least 5 characters",
                    "param": "text",
                },
            },
            status_code=400,
        )

        with Pincho(token="abc12345") as client:
            with pytest.raises(ValidationError) as exc_info:
                client.notifai("hi")
            assert "text_too_short" in str(exc_info.value)
