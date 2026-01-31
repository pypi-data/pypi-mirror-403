"""Error handling decorators and context managers."""

from __future__ import annotations

import functools
import logging
from contextlib import contextmanager
from typing import Any, Callable, TypeVar, ParamSpec

import httpx

from .types import TimeoutError, NetworkError
from .mappings import parse_api_error

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


@contextmanager
def handle_api_errors():
    """Context manager to catch and convert httpx errors to SDK exceptions.

    Usage:
        with handle_api_errors():
            result = self._api.analyze_create(request)
        return result
    """
    try:
        yield
    except httpx.HTTPStatusError as e:
        # Parse error body
        try:
            error_body = e.response.json()
        except Exception:
            error_body = e.response.text

        logger.debug("API error: status=%d, body=%s", e.response.status_code, error_body)
        raise parse_api_error(
            status_code=e.response.status_code,
            error_body=error_body,
            original_error=e,
        ) from e
    except httpx.TimeoutException as e:
        logger.debug("Timeout error: %s", e)
        raise TimeoutError(
            message="Request timed out",
            suggestion="Try increasing the timeout: SDKRouter(timeout=120.0)",
            original_error=e,
        ) from e
    except httpx.ConnectError as e:
        logger.debug("Connection error: %s", e)
        raise NetworkError(
            message=f"Failed to connect: {e}",
            suggestion="Check your internet connection and API URL.",
            original_error=e,
        ) from e
    except httpx.RequestError as e:
        logger.debug("Request error: %s", e)
        raise NetworkError(
            message=f"Network error: {e}",
            original_error=e,
        ) from e


def api_error_handler(func: Callable[P, T]) -> Callable[P, T]:
    """Decorator to wrap API calls with error handling.

    Usage:
        @api_error_handler
        def analyze(self, *, image_url: str) -> VisionAnalyzeResponse:
            return self._api.analyze_create(request)
    """
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        with handle_api_errors():
            return func(*args, **kwargs)
    return wrapper


def async_api_error_handler(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to wrap async API calls with error handling.

    Usage:
        @async_api_error_handler
        async def analyze(self, *, image_url: str) -> VisionAnalyzeResponse:
            return await self._api.analyze_create(request)
    """
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except httpx.HTTPStatusError as e:
            try:
                error_body = e.response.json()
            except Exception:
                error_body = e.response.text

            logger.debug("API error: status=%d, body=%s", e.response.status_code, error_body)
            raise parse_api_error(
                status_code=e.response.status_code,
                error_body=error_body,
                original_error=e,
            ) from e
        except httpx.TimeoutException as e:
            logger.debug("Timeout error: %s", e)
            raise TimeoutError(
                message="Request timed out",
                suggestion="Try increasing the timeout: SDKRouter(timeout=120.0)",
                original_error=e,
            ) from e
        except httpx.ConnectError as e:
            logger.debug("Connection error: %s", e)
            raise NetworkError(
                message=f"Failed to connect: {e}",
                suggestion="Check your internet connection and API URL.",
                original_error=e,
            ) from e
        except httpx.RequestError as e:
            logger.debug("Request error: %s", e)
            raise NetworkError(
                message=f"Network error: {e}",
                original_error=e,
            ) from e
    return wrapper
