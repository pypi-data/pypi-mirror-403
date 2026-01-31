"""Custom exceptions for Pincho library."""


class PinchoError(Exception):
    """Base exception for Pincho library.

    All other exceptions in this library inherit from this class.

    Attributes:
        is_retryable: Whether this error indicates a transient issue that may succeed on retry
    """

    is_retryable: bool = False


class AuthenticationError(PinchoError):
    """Raised when authentication fails.

    This typically occurs when:
    - The API token is invalid or expired
    - The token doesn't have permission
    - The account is disabled

    This error is NOT retryable as credentials won't change between attempts.
    """

    is_retryable = False


class ValidationError(PinchoError):
    """Raised when request validation fails.

    This typically occurs when:
    - Required parameters are missing
    - Parameters have invalid values
    - The request format is incorrect

    This error is NOT retryable as the same invalid request will fail again.
    """

    is_retryable = False


class RateLimitError(PinchoError):
    """Raised when rate limit is exceeded (HTTP 429).

    This error IS retryable with exponential backoff.
    The client will automatically retry with longer delays.
    """

    is_retryable = True


class ServerError(PinchoError):
    """Raised when server returns 5xx error.

    This typically indicates temporary server issues.
    This error IS retryable with exponential backoff.
    """

    is_retryable = True


class NetworkError(PinchoError):
    """Raised when network communication fails.

    This typically occurs when:
    - Network connection is unavailable
    - DNS resolution fails
    - Connection timeouts

    This error IS retryable with exponential backoff.
    """

    is_retryable = True
