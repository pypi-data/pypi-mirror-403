from __future__ import annotations

import httpx

from .models import (
    RankedResults,
    SearchAsyncRequestRequest,
    SearchAsyncResponse,
    SearchJobStatus,
    SearchModeResponse,
    SearchQueryRequest,
    SearchRequestList,
    SearchRequestListRequest,
    SearchResponse,
    URLFetchRequest,
)


class SearchSearchAPI:
    """API endpoints for Search."""

    def __init__(self, client: httpx.AsyncClient):
        """Initialize sub-client with shared httpx client."""
        self._client = client

    async def list(
        self,
        ordering: str | None = None,
        search: str | None = None,
    ) -> list[SearchRequestList]:
        """
        List search history

        List search history for the current API key.
        """
        url = "/api/search/"
        response = await self._client.get(url, params={"ordering": ordering if ordering is not None else None, "search": search if search is not None else None})
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return [SearchRequestList.model_validate(item) for item in response.json()]


    async def cancel_create(self, uuid: str, data: SearchRequestListRequest) -> None:
        """
        Cancel async search job

        Cancel a queued or running search job.
        """
        url = f"/api/search/{uuid}/cancel/"
        response = await self._client.post(url, json=data.model_dump(exclude_unset=True))
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return None


    async def rankings_retrieve(self, uuid: str) -> RankedResults:
        """
        Get ranked results

        Get ranked results from completed search job.
        """
        url = f"/api/search/{uuid}/rankings/"
        response = await self._client.get(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return RankedResults.model_validate(response.json())


    async def results_retrieve(self, uuid: str) -> SearchModeResponse:
        """
        Get full results

        Get all results from completed search job based on mode.
        """
        url = f"/api/search/{uuid}/results/"
        response = await self._client.get(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return SearchModeResponse.model_validate(response.json())


    async def status_retrieve(self, uuid: str) -> SearchJobStatus:
        """
        Get job status

        Get status of async search job.
        """
        url = f"/api/search/{uuid}/status/"
        response = await self._client.get(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return SearchJobStatus.model_validate(response.json())


    async def fetch_create(self, data: URLFetchRequest) -> SearchResponse:
        """
        Fetch and analyze URL

        Fetch and analyze URL content using Claude.
        """
        url = "/api/search/fetch/"
        response = await self._client.post(url, json=data.model_dump(exclude_unset=True))
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return SearchResponse.model_validate(response.json())


    async def query_create(self, data: SearchQueryRequest) -> SearchResponse:
        """
        Execute web search

        Execute a web search using Anthropic's web_search tool.
        """
        url = "/api/search/query/"
        response = await self._client.post(url, json=data.model_dump(exclude_unset=True))
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return SearchResponse.model_validate(response.json())


    async def query_async_create(
        self,
        data: SearchAsyncRequestRequest,
    ) -> SearchAsyncResponse:
        """
        Execute async search

        Queue search with specified mode for analysis depth.
        """
        url = "/api/search/query-async/"
        response = await self._client.post(url, json=data.model_dump(exclude_unset=True))
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return SearchAsyncResponse.model_validate(response.json())


