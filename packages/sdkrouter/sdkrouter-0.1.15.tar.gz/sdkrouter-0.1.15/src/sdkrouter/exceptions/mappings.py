"""Error code mappings and API error parsing."""

from __future__ import annotations

from typing import Any

from .types import (
    SDKRouterError,
    APIError,
    ImageFetchError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError,
)


# Error code to exception class mapping
ERROR_CODE_MAP: dict[str, type[SDKRouterError]] = {
    "IMAGE_FETCH_ERROR": ImageFetchError,
    "AUTHENTICATION_ERROR": AuthenticationError,
    "INVALID_API_KEY": AuthenticationError,
    "RATE_LIMIT_EXCEEDED": RateLimitError,
    "VALIDATION_ERROR": ValidationError,
}

# Suggestions for specific error codes
ERROR_SUGGESTIONS: dict[str, str] = {
    "IMAGE_FETCH_ERROR": (
        "The server couldn't fetch the image from URL. Try using image_path instead:\n"
        "  result = client.vision.analyze(\n"
        "      image_path=Path('./your_image.jpg'),  # Upload directly\n"
        "      prompt='Describe this image',\n"
        "  )"
    ),
    "AUTHENTICATION_ERROR": (
        "Check your API key:\n"
        "  client = SDKRouter(api_key='your-api-key')\n"
        "Or set SDKROUTER_API_KEY environment variable."
    ),
    "INVALID_API_KEY": (
        "Check your API key:\n"
        "  client = SDKRouter(api_key='your-api-key')\n"
        "Or set SDKROUTER_API_KEY environment variable."
    ),
    "RATE_LIMIT_EXCEEDED": "Wait a moment and retry, or contact support to increase your rate limit.",
    "NOT_FOUND": (
        "The API endpoint was not found. This usually means:\n"
        "1. The endpoint is not deployed on the server yet\n"
        "2. You're using production URL but need to test locally\n\n"
        "For local development, set:\n"
        "  export SDKROUTER_API_URL=http://127.0.0.1:8000\n"
        "Or:\n"
        "  client = SDKRouter(api_url='http://127.0.0.1:8000')"
    ),
}


def parse_api_error(
    status_code: int,
    error_body: dict[str, Any] | str,
    original_error: Exception | None = None,
) -> SDKRouterError:
    """Parse API error response and return appropriate exception.

    Args:
        status_code: HTTP status code
        error_body: Error response body (dict or string)
        original_error: Original httpx exception

    Returns:
        Appropriate SDKRouterError subclass
    """
    # Extract error code and message
    if isinstance(error_body, dict):
        error_code = error_body.get("error") or error_body.get("code")
        # error_code must be a string for dict lookup; nested dicts are not valid codes
        if not isinstance(error_code, str):
            error_code = None
        message = error_body.get("message") or error_body.get("detail") or str(error_body)
    else:
        error_code = None
        message = str(error_body)

    # Get suggestion for this error code
    suggestion = ERROR_SUGGESTIONS.get(error_code) if error_code else None

    # Map to specific exception class
    exception_class = APIError
    if error_code and error_code in ERROR_CODE_MAP:
        exception_class = ERROR_CODE_MAP[error_code]
    elif status_code == 401:
        exception_class = AuthenticationError
        suggestion = suggestion or ERROR_SUGGESTIONS.get("AUTHENTICATION_ERROR")
    elif status_code == 429:
        exception_class = RateLimitError
        suggestion = suggestion or ERROR_SUGGESTIONS.get("RATE_LIMIT_EXCEEDED")
    elif status_code == 404:
        exception_class = NotFoundError
        # For HTML 404 pages, provide a cleaner message
        if isinstance(error_body, str) and "<!doctype" in error_body.lower():
            message = "Endpoint not found (404)"
        suggestion = suggestion or ERROR_SUGGESTIONS.get("NOT_FOUND")
    elif status_code == 422:
        exception_class = ValidationError

    return exception_class(
        message=message,
        error_code=error_code,
        status_code=status_code,
        suggestion=suggestion,
        original_error=original_error,
    )
