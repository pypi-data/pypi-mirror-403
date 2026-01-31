"""Asynchronous Pincho client."""

import asyncio
import logging
import os
from datetime import datetime
from typing import List, Optional

import httpx

from pincho import __version__
from pincho.crypto import encrypt_message, generate_iv
from pincho.exceptions import (
    AuthenticationError,
    NetworkError,
    PinchoError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from pincho.models import (
    NotifAIRequest,
    NotifAIResponse,
    NotificationRequest,
    NotificationResponse,
    RateLimitInfo,
)
from pincho.validation import normalize_tags

logger = logging.getLogger("pincho")


class AsyncPincho:
    """Asynchronous Pincho client for v1 API.

    This client provides async/await support for sending notifications and
    AI-powered notification generation.

    Features:
        - Automatic retry logic with exponential backoff
        - Tag normalization and validation
        - Message encryption support
        - Comprehensive error handling
        - Debug logging support

    Example:
        >>> import asyncio
        >>> async def main():
        ...     async with AsyncPincho(token='abc12345') as client:
        ...         await client.send('Build Complete', 'Deployed successfully')
        >>> asyncio.run(main())
    """

    BASE_URL = "https://api.pincho.app"
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_MAX_RETRIES = 3
    MAX_BACKOFF = 30.0  # Maximum retry delay in seconds

    def __init__(
        self,
        token: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        base_url: Optional[str] = None,
    ):
        """Initialize async Pincho client.

        Args:
            token: Pincho API token. If not provided, reads from PINCHO_TOKEN env var.
            timeout: Request timeout in seconds. If not provided, reads from PINCHO_TIMEOUT
                    env var or defaults to 30.0.
            max_retries: Maximum number of retry attempts. If not provided, reads from
                        PINCHO_MAX_RETRIES env var or defaults to 3. Set to 0 to disable.
            base_url: Optional custom base URL (mainly for testing)

        Raises:
            ValueError: If token is not provided and PINCHO_TOKEN env var is not set

        Examples:
            >>> # Auto-load from environment variables
            >>> client = AsyncPincho()  # reads PINCHO_TOKEN

            >>> # Explicit token
            >>> client = AsyncPincho(token='abc12345')

            >>> # With custom settings
            >>> client = AsyncPincho(
            ...     token='abc12345',
            ...     timeout=60.0,
            ...     max_retries=5
            ... )
        """
        # Load from environment variables with fallbacks
        resolved_token = token or os.environ.get("PINCHO_TOKEN")
        if not resolved_token:
            raise ValueError(
                "Token is required. Provide token parameter or set "
                "PINCHO_TOKEN environment variable."
            )

        # Parse timeout from env var if not provided
        if timeout is not None:
            resolved_timeout = timeout
        else:
            env_timeout = os.environ.get("PINCHO_TIMEOUT")
            resolved_timeout = float(env_timeout) if env_timeout else self.DEFAULT_TIMEOUT

        # Parse max_retries from env var if not provided
        if max_retries is not None:
            resolved_max_retries = max_retries
        else:
            env_retries = os.environ.get("PINCHO_MAX_RETRIES")
            resolved_max_retries = int(env_retries) if env_retries else self.DEFAULT_MAX_RETRIES

        self.token = resolved_token
        self.timeout = resolved_timeout
        self.max_retries = resolved_max_retries
        self.base_url = base_url or self.BASE_URL
        self._client = httpx.AsyncClient(
            timeout=resolved_timeout,
            headers={"User-Agent": f"pincho-python/{__version__}"},
        )
        self.last_rate_limit: Optional[RateLimitInfo] = None

        logger.debug(
            "AsyncPincho initialized with token=%s, timeout=%s, max_retries=%s",
            resolved_token[:8] + "..." if len(resolved_token) > 8 else resolved_token,
            resolved_timeout,
            resolved_max_retries,
        )

    async def __aenter__(self) -> "AsyncPincho":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        await self._client.aclose()
        logger.debug("AsyncPincho client closed")

    async def send(
        self,
        title: str,
        message: str,
        *,
        type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        image_url: Optional[str] = None,
        action_url: Optional[str] = None,
        encryption_password: Optional[str] = None,
    ) -> NotificationResponse:
        """Send a notification via Pincho v1 API (async).

        Args:
            title: Notification title
            message: Notification message body
            type: Optional notification type for filtering/organization
            tags: Optional list of tags (will be normalized: lowercased, trimmed, deduplicated)
            image_url: Optional image URL to display with notification
            action_url: Optional URL to open when notification is tapped
            encryption_password: Optional password for AES-128-CBC encryption
                (must match type configuration in app)

        Returns:
            NotificationResponse with status and message

        Raises:
            AuthenticationError: Invalid token
            ValidationError: Invalid parameters (missing required fields, etc.)
            RateLimitError: Rate limit exceeded (429)
            ServerError: Server error (5xx)
            NetworkError: Network communication failure
            PinchoError: Other API errors

        Example:
            >>> async with AsyncPincho(token='abc12345') as client:
            ...     response = await client.send(
            ...         'Deploy Complete',
            ...         'v1.2.3 deployed to production',
            ...         type='deployment',
            ...         tags=['production', 'release']
            ...     )
            ...     print(response.status)  # 'success'

        Example with encryption:
            >>> async with AsyncPincho(token='abc12345') as client:
            ...     response = await client.send(
            ...         'Secure Message',
            ...         'Sensitive data here',
            ...         type='secure',
            ...         encryption_password='your_password'
            ...     )
        """
        # Normalize tags
        normalized_tags = normalize_tags(tags) or None
        if normalized_tags != tags and tags:
            logger.debug("Tags normalized: %s -> %s", tags, normalized_tags)

        # Handle encryption if password provided
        final_message = message
        iv_hex: Optional[str] = None

        if encryption_password:
            iv_bytes, iv_hex = generate_iv()
            final_message = encrypt_message(message, encryption_password, iv_bytes)
            logger.debug("Message encrypted with IV: %s", iv_hex)

        request = NotificationRequest(
            title=title,
            message=final_message,
            type=type,
            tags=normalized_tags,
            imageURL=image_url,
            actionURL=action_url,
            iv=iv_hex,
        )

        return await self._send_with_retry(request)

    async def notifai(
        self,
        text: str,
        *,
        type: Optional[str] = None,
    ) -> NotifAIResponse:
        """Generate and send AI-powered notification from free-form text.

        Uses Gemini AI to convert natural language into a structured notification
        with auto-generated title, message, tags, and action URL.

        Args:
            text: Free-form text to convert into notification
            type: Optional notification type (overrides AI-generated type)

        Returns:
            NotifAIResponse with status, message, and generated notification details

        Raises:
            AuthenticationError: Invalid token
            ValidationError: Invalid parameters
            RateLimitError: Rate limit exceeded (429)
            ServerError: Server error (5xx)
            NetworkError: Network communication failure
            PinchoError: Other API errors

        Example:
            >>> async with AsyncPincho(token='abc12345') as client:
            ...     response = await client.notifai(
            ...         'deployment finished successfully, v2.1.3 is live on prod'
            ...     )
            ...     print(response.status)  # 'success'
            ...     print(response.notification)  # AI-generated structured notification
        """
        request = NotifAIRequest(
            text=text,
            type=type,
        )

        return await self._notifai_with_retry(request)

    async def _send_with_retry(self, request: NotificationRequest) -> NotificationResponse:
        """Send request with automatic retry logic.

        Args:
            request: NotificationRequest to send

        Returns:
            NotificationResponse from API

        Raises:
            Various PinchoError subclasses based on error type
        """
        attempt = 0
        last_exception: Optional[Exception] = None

        while attempt <= self.max_retries:
            try:
                logger.debug("Send attempt %d/%d", attempt + 1, self.max_retries + 1)

                response = await self._client.post(
                    f"{self.base_url}/send",
                    json=request.to_dict(),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.token}",
                    },
                )

                # Parse rate limit headers from response
                self.last_rate_limit = self._parse_rate_limit_headers(response)
                if self.last_rate_limit:
                    logger.debug(
                        "Rate limit info: %d/%d remaining, resets at %s",
                        self.last_rate_limit.remaining,
                        self.last_rate_limit.limit,
                        self.last_rate_limit.reset,
                    )

                response.raise_for_status()

                data = response.json()
                logger.info("Notification sent successfully: %s", request.title)
                return NotificationResponse(
                    status=data.get("status", "unknown"),
                    message=data.get("message", ""),
                )

            except httpx.HTTPStatusError as e:
                last_exception = e

                # Parse rate limit headers even on error responses
                self.last_rate_limit = self._parse_rate_limit_headers(e.response)

                error = self._handle_http_error(e)

                # Don't retry non-retryable errors
                if not error.is_retryable:
                    raise error from e

                # Retry logic for retryable errors
                if attempt < self.max_retries:
                    # Use Retry-After header if available for rate limits
                    if isinstance(error, RateLimitError):
                        retry_after = e.response.headers.get("Retry-After")
                        if retry_after:
                            try:
                                backoff = float(retry_after)
                                logger.debug("Using Retry-After header: %.1fs", backoff)
                            except ValueError:
                                backoff = self._calculate_backoff(attempt, is_rate_limit=True)
                        else:
                            backoff = self._calculate_backoff(attempt, is_rate_limit=True)
                    else:
                        backoff = self._calculate_backoff(attempt, is_rate_limit=False)

                    logger.warning(
                        "Retryable error (attempt %d/%d): %s. Retrying in %.1fs",
                        attempt + 1,
                        self.max_retries + 1,
                        error,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    attempt += 1
                else:
                    raise error from e

            except httpx.RequestError as e:
                last_exception = e
                error = NetworkError(f"Network error: {str(e)}")

                if attempt < self.max_retries:
                    backoff = self._calculate_backoff(attempt, is_rate_limit=False)
                    logger.warning(
                        "Network error (attempt %d/%d): %s. Retrying in %.1fs",
                        attempt + 1,
                        self.max_retries + 1,
                        e,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    attempt += 1
                else:
                    raise error from e

            except Exception as e:
                last_exception = e
                raise PinchoError(f"Unexpected error: {str(e)}") from e

        # Should never reach here, but just in case
        raise PinchoError(f"Failed after {self.max_retries + 1} attempts") from last_exception

    async def _notifai_with_retry(self, request: NotifAIRequest) -> NotifAIResponse:
        """Send NotifAI request with automatic retry logic.

        Args:
            request: NotifAIRequest to send

        Returns:
            NotifAIResponse from API

        Raises:
            Various PinchoError subclasses based on error type
        """
        attempt = 0
        last_exception: Optional[Exception] = None

        while attempt <= self.max_retries:
            try:
                logger.debug("NotifAI attempt %d/%d", attempt + 1, self.max_retries + 1)

                response = await self._client.post(
                    f"{self.base_url}/notifai",
                    json=request.to_dict(),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.token}",
                    },
                )

                # Parse rate limit headers from response
                self.last_rate_limit = self._parse_rate_limit_headers(response)
                if self.last_rate_limit:
                    logger.debug(
                        "Rate limit info: %d/%d remaining, resets at %s",
                        self.last_rate_limit.remaining,
                        self.last_rate_limit.limit,
                        self.last_rate_limit.reset,
                    )

                response.raise_for_status()

                data = response.json()
                logger.info("NotifAI notification generated successfully")
                return NotifAIResponse(
                    status=data.get("status", "unknown"),
                    message=data.get("message", ""),
                    notification=data.get("notification"),
                )

            except httpx.HTTPStatusError as e:
                last_exception = e

                # Parse rate limit headers even on error responses
                self.last_rate_limit = self._parse_rate_limit_headers(e.response)

                error = self._handle_http_error(e)

                # Don't retry non-retryable errors
                if not error.is_retryable:
                    raise error from e

                # Retry logic for retryable errors
                if attempt < self.max_retries:
                    # Use Retry-After header if available for rate limits
                    if isinstance(error, RateLimitError):
                        retry_after = e.response.headers.get("Retry-After")
                        if retry_after:
                            try:
                                backoff = float(retry_after)
                                logger.debug("Using Retry-After header: %.1fs", backoff)
                            except ValueError:
                                backoff = self._calculate_backoff(attempt, is_rate_limit=True)
                        else:
                            backoff = self._calculate_backoff(attempt, is_rate_limit=True)
                    else:
                        backoff = self._calculate_backoff(attempt, is_rate_limit=False)

                    logger.warning(
                        "Retryable error (attempt %d/%d): %s. Retrying in %.1fs",
                        attempt + 1,
                        self.max_retries + 1,
                        error,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    attempt += 1
                else:
                    raise error from e

            except httpx.RequestError as e:
                last_exception = e
                error = NetworkError(f"Network error: {str(e)}")

                if attempt < self.max_retries:
                    backoff = self._calculate_backoff(attempt, is_rate_limit=False)
                    logger.warning(
                        "Network error (attempt %d/%d): %s. Retrying in %.1fs",
                        attempt + 1,
                        self.max_retries + 1,
                        e,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    attempt += 1
                else:
                    raise error from e

            except Exception as e:
                last_exception = e
                raise PinchoError(f"Unexpected error: {str(e)}") from e

        # Should never reach here, but just in case
        raise PinchoError(f"Failed after {self.max_retries + 1} attempts") from last_exception

    def _handle_http_error(self, error: httpx.HTTPStatusError) -> PinchoError:
        """Convert HTTP status errors to appropriate Pincho exceptions.

        Args:
            error: HTTPStatusError from httpx

        Returns:
            Appropriate PinchoError subclass
        """
        status_code = error.response.status_code

        # Extract error message from response (nested error format only)
        try:
            error_data = error.response.json()
            error_obj = error_data.get("error", {})
            error_message = error_obj.get("message", "Unknown error")
            error_code = error_obj.get("code")
            error_param = error_obj.get("param")

            # Build descriptive message
            if error_code:
                error_message = f"{error_message} [{error_code}]"
            if error_param:
                error_message = f"{error_message} (parameter: {error_param})"
        except Exception:
            error_message = error.response.text

        # Authentication errors (401, 403)
        if status_code == 401:
            return AuthenticationError(
                f"Invalid token. Please check your credentials. {error_message}"
            )

        if status_code == 403:
            return AuthenticationError(
                f"Forbidden: Your account may be disabled or you don't have "
                f"permission. {error_message}"
            )

        # Validation errors (400, 404)
        if status_code == 400:
            return ValidationError(f"Invalid parameters: {error_message}")

        if status_code == 404:
            return ValidationError(f"Resource not found. {error_message}")

        # Rate limit (429)
        if status_code == 429:
            return RateLimitError(f"Rate limit exceeded: {error_message}")

        # Server errors (5xx)
        if 500 <= status_code < 600:
            return ServerError(f"Server error ({status_code}): {error_message}")

        # Other errors
        return PinchoError(f"API error ({status_code}): {error_message}")

    def _calculate_backoff(self, attempt: int, is_rate_limit: bool) -> float:
        """Calculate exponential backoff delay.

        Args:
            attempt: Current attempt number (0-indexed)
            is_rate_limit: Whether this is a rate limit error (uses longer backoff)

        Returns:
            Delay in seconds before next retry
        """
        if is_rate_limit:
            # Rate limit: longer backoff (5s, 10s, 20s, ...)
            base_delay = 5.0
        else:
            # Normal errors: standard backoff (1s, 2s, 4s, 8s, ...)
            base_delay = 1.0

        delay = base_delay * (2**attempt)
        return float(min(delay, self.MAX_BACKOFF))

    def _parse_rate_limit_headers(self, response: httpx.Response) -> Optional[RateLimitInfo]:
        """Parse rate limit headers from API response.

        Args:
            response: HTTP response from API

        Returns:
            RateLimitInfo if all headers present, None otherwise
        """
        limit = response.headers.get("RateLimit-Limit")
        remaining = response.headers.get("RateLimit-Remaining")
        reset = response.headers.get("RateLimit-Reset")

        if limit and remaining and reset:
            try:
                return RateLimitInfo(
                    limit=int(limit),
                    remaining=int(remaining),
                    reset=datetime.fromtimestamp(int(reset)),
                )
            except (ValueError, TypeError, OSError) as e:
                logger.debug("Failed to parse rate limit headers: %s", e)
                return None
        return None
