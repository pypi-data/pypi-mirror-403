"""URL shortening tool using generated API client."""

import logging
from datetime import datetime
from typing import Any

import httpx

from .._config import SDKConfig
from ..exceptions import api_error_handler, async_api_error_handler

logger = logging.getLogger(__name__)
from .._api.client import (
    BaseResource,
    AsyncBaseResource,
    SyncShortlinksShortlinksAPI,
    ShortlinksShortlinksAPI,
)
from .._api.generated.shortlinks.shortlinks__api__shortlinks.models import (
    ShortLinkList,
    ShortLinkDetail,
    ShortLinkCreate,
    ShortLinkCreateRequest,
    PaginatedShortLinkListList,
    ShortLinkStats,
)


class ShortlinksResource(BaseResource):
    """URL shortening tool (sync).

    Uses generated SyncShortlinksShortlinksAPI client.
    """

    def __init__(self, config: SDKConfig):
        super().__init__(config)
        self._api = SyncShortlinksShortlinksAPI(self._http_client)

    @api_error_handler
    def create(
        self,
        target_url: str,
        *,
        custom_slug: str | None = None,
        expires_at: datetime | None = None,
        max_hits: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ShortLinkCreate:
        """
        Create a short link.

        Args:
            target_url: URL to redirect to
            custom_slug: Custom slug (optional)
            expires_at: Expiration datetime (optional)
            max_hits: Max redirects (optional)
            metadata: Additional metadata

        Returns:
            ShortLinkCreate with link info.
        """
        logger.debug("Creating shortlink: target=%s, slug=%s", target_url, custom_slug)
        # Build request with only non-None values
        kwargs: dict[str, Any] = {"target_url": target_url}
        if custom_slug is not None:
            kwargs["custom_slug"] = custom_slug
        if expires_at is not None:
            kwargs["expires_at"] = expires_at.isoformat()
        if max_hits is not None:
            kwargs["max_hits"] = max_hits
        if metadata is not None:
            kwargs["metadata"] = metadata
        request = ShortLinkCreateRequest(**kwargs)  # type: ignore[arg-type]
        result = self._api.create(request)
        logger.info("Shortlink created for: %s", target_url)
        return result

    @api_error_handler
    def get(self, code: str) -> ShortLinkDetail:
        """Get link details by code."""
        return self._api.retrieve(code)

    @api_error_handler
    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedShortLinkListList:
        """List short links."""
        return self._api.list(page=page, page_size=page_size)  # type: ignore[return-value]

    @api_error_handler
    def delete(self, code: str) -> bool:
        """Deactivate a short link."""
        logger.debug("Deleting shortlink: %s", code)
        self._api.destroy(code)
        logger.info("Shortlink deleted: %s", code)
        return True

    @api_error_handler
    def stats(self) -> ShortLinkStats:
        """Get link statistics."""
        return self._api.stats_retrieve()


class AsyncShortlinksResource(AsyncBaseResource):
    """URL shortening tool (async).

    Uses generated ShortlinksShortlinksAPI client.
    """

    def __init__(self, config: SDKConfig):
        super().__init__(config)
        self._api = ShortlinksShortlinksAPI(self._http_client)

    @async_api_error_handler
    async def create(
        self,
        target_url: str,
        *,
        custom_slug: str | None = None,
        expires_at: datetime | None = None,
        max_hits: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ShortLinkCreate:
        """Create a short link."""
        logger.debug("Creating shortlink: target=%s, slug=%s", target_url, custom_slug)
        # Build request with only non-None values
        kwargs: dict[str, Any] = {"target_url": target_url}
        if custom_slug is not None:
            kwargs["custom_slug"] = custom_slug
        if expires_at is not None:
            kwargs["expires_at"] = expires_at.isoformat()
        if max_hits is not None:
            kwargs["max_hits"] = max_hits
        if metadata is not None:
            kwargs["metadata"] = metadata
        request = ShortLinkCreateRequest(**kwargs)  # type: ignore[arg-type]
        result = await self._api.create(request)
        logger.info("Shortlink created for: %s", target_url)
        return result

    @async_api_error_handler
    async def get(self, code: str) -> ShortLinkDetail:
        """Get link details by code."""
        return await self._api.retrieve(code)

    @async_api_error_handler
    async def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedShortLinkListList:
        """List short links."""
        return await self._api.list(page=page, page_size=page_size)  # type: ignore[return-value]

    @async_api_error_handler
    async def delete(self, code: str) -> bool:
        """Deactivate a short link."""
        logger.debug("Deleting shortlink: %s", code)
        await self._api.destroy(code)
        logger.info("Shortlink deleted: %s", code)
        return True

    @async_api_error_handler
    async def stats(self) -> ShortLinkStats:
        """Get link statistics."""
        return await self._api.stats_retrieve()


__all__ = [
    "ShortlinksResource",
    "AsyncShortlinksResource",
    # Models
    "ShortLinkList",
    "ShortLinkDetail",
    "ShortLinkCreate",
    "ShortLinkCreateRequest",
    "PaginatedShortLinkListList",
    "ShortLinkStats",
]
