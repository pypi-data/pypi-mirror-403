from __future__ import annotations

import httpx

from .models import (
    PaginatedShortLinkListList,
    ShortLinkCreate,
    ShortLinkCreateRequest,
    ShortLinkDetail,
    ShortLinkList,
    ShortLinkStats,
)


class SyncShortlinksShortlinksAPI:
    """Synchronous API endpoints for Shortlinks."""

    def __init__(self, client: httpx.Client):
        """Initialize sync sub-client with shared httpx client."""
        self._client = client

    def list(
        self,
        ordering: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        search: str | None = None,
    ) -> list[PaginatedShortLinkListList]:
        """
        ViewSet for short link management. Endpoints: - GET /api/shortlinks/ -
        List user's short links - POST /api/shortlinks/ - Create a new short
        link - GET /api/shortlinks/{code}/ - Get short link details - DELETE
        /api/shortlinks/{code}/ - Deactivate short link - GET
        /api/shortlinks/stats/ - Get link statistics
        """
        url = "/api/shortlinks/"
        _params = {
            "ordering": ordering if ordering is not None else None,
            "page": page if page is not None else None,
            "page_size": page_size if page_size is not None else None,
            "search": search if search is not None else None,
        }
        response = self._client.get(url, params=_params)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return PaginatedShortLinkListList.model_validate(response.json())


    def create(self, data: ShortLinkCreateRequest) -> ShortLinkCreate:
        """
        Create a new short link.
        """
        url = "/api/shortlinks/"
        response = self._client.post(url, json=data.model_dump(exclude_unset=True))
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return ShortLinkCreate.model_validate(response.json())


    def retrieve(self, code: str) -> ShortLinkDetail:
        """
        ViewSet for short link management. Endpoints: - GET /api/shortlinks/ -
        List user's short links - POST /api/shortlinks/ - Create a new short
        link - GET /api/shortlinks/{code}/ - Get short link details - DELETE
        /api/shortlinks/{code}/ - Deactivate short link - GET
        /api/shortlinks/stats/ - Get link statistics
        """
        url = f"/api/shortlinks/{code}/"
        response = self._client.get(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return ShortLinkDetail.model_validate(response.json())


    def update(self, code: str) -> ShortLinkList:
        """
        ViewSet for short link management. Endpoints: - GET /api/shortlinks/ -
        List user's short links - POST /api/shortlinks/ - Create a new short
        link - GET /api/shortlinks/{code}/ - Get short link details - DELETE
        /api/shortlinks/{code}/ - Deactivate short link - GET
        /api/shortlinks/stats/ - Get link statistics
        """
        url = f"/api/shortlinks/{code}/"
        response = self._client.put(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return ShortLinkList.model_validate(response.json())


    def partial_update(self, code: str) -> ShortLinkList:
        """
        ViewSet for short link management. Endpoints: - GET /api/shortlinks/ -
        List user's short links - POST /api/shortlinks/ - Create a new short
        link - GET /api/shortlinks/{code}/ - Get short link details - DELETE
        /api/shortlinks/{code}/ - Deactivate short link - GET
        /api/shortlinks/stats/ - Get link statistics
        """
        url = f"/api/shortlinks/{code}/"
        response = self._client.patch(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return ShortLinkList.model_validate(response.json())


    def destroy(self, code: str) -> None:
        """
        Deactivate a short link.
        """
        url = f"/api/shortlinks/{code}/"
        response = self._client.delete(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )


    def stats_retrieve(self) -> ShortLinkStats:
        """
        Get shortlink statistics

        Get shortlink statistics for the current user.
        """
        url = "/api/shortlinks/stats/"
        response = self._client.get(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return ShortLinkStats.model_validate(response.json())


