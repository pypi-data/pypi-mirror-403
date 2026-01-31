"""SDKRouter exceptions with helpful error messages."""

from .types import (
    SDKRouterError,
    APIError,
    ImageFetchError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    TimeoutError,
    NetworkError,
    NotFoundError,
)
from .mappings import (
    ERROR_CODE_MAP,
    ERROR_SUGGESTIONS,
    parse_api_error,
)
from .handlers import (
    handle_api_errors,
    api_error_handler,
    async_api_error_handler,
)

__all__ = [
    # Exception classes
    "SDKRouterError",
    "APIError",
    "ImageFetchError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "TimeoutError",
    "NetworkError",
    "NotFoundError",
    # Utilities
    "parse_api_error",
    "handle_api_errors",
    "api_error_handler",
    "async_api_error_handler",
    "ERROR_CODE_MAP",
    "ERROR_SUGGESTIONS",
]
