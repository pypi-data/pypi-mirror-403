"""SDKRouter exception classes."""

from __future__ import annotations


class SDKRouterError(Exception):
    """Base exception for all SDKRouter errors."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str | None = None,
        status_code: int | None = None,
        suggestion: str | None = None,
        original_error: Exception | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.suggestion = suggestion
        self.original_error = original_error

        # Build full message
        full_message = message
        if suggestion:
            full_message = f"{message}\n\nSuggestion: {suggestion}"

        super().__init__(full_message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, error_code={self.error_code!r})"


class APIError(SDKRouterError):
    """Error from API response."""

    pass


class ImageFetchError(SDKRouterError):
    """Server failed to fetch image from URL.

    This happens when:
    - The image URL is not accessible from the server
    - The server has network issues (firewall, DNS, timeout)
    - The image host blocks server requests

    Solution: Use image_path to upload local file instead.
    """

    pass


class AuthenticationError(SDKRouterError):
    """Invalid or missing API key."""

    pass


class RateLimitError(SDKRouterError):
    """Rate limit exceeded."""

    pass


class ValidationError(SDKRouterError):
    """Invalid request parameters."""

    pass


class TimeoutError(SDKRouterError):
    """Request timed out."""

    pass


class NetworkError(SDKRouterError):
    """Network connection error."""

    pass


class NotFoundError(SDKRouterError):
    """Resource or endpoint not found (404).

    This usually means:
    - The API endpoint doesn't exist (wrong URL)
    - The resource (UUID) doesn't exist
    - The server is not configured correctly

    For local development, set:
        SDKROUTER_API_URL=http://127.0.0.1:8000
    """

    pass
