from __future__ import annotations

import httpx

from .models import (
    PaginatedSDKAPIKeyListList,
    SDKAPIKeyCreate,
    SDKAPIKeyCreateRequest,
    SDKAPIKeyDetail,
    SDKAPIKeyList,
)


class SdkKeysSdkKeysAPI:
    """API endpoints for Sdk Keys."""

    def __init__(self, client: httpx.AsyncClient):
        """Initialize sub-client with shared httpx client."""
        self._client = client

    async def list(
        self,
        ordering: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        search: str | None = None,
    ) -> list[PaginatedSDKAPIKeyListList]:
        """
        ViewSet for SDK API key management. Endpoints: - GET /api/sdk_keys/ -
        List user's SDK API keys - POST /api/sdk_keys/ - Create a new SDK API
        key - GET /api/sdk_keys/{id}/ - Get SDK API key details - DELETE
        /api/sdk_keys/{id}/ - Deactivate SDK API key - POST
        /api/sdk_keys/{id}/rotate/ - Rotate SDK API key - POST
        /api/sdk_keys/{id}/reactivate/ - Reactivate SDK API key
        """
        url = "/api/sdk_keys/"
        _params = {
            "ordering": ordering if ordering is not None else None,
            "page": page if page is not None else None,
            "page_size": page_size if page_size is not None else None,
            "search": search if search is not None else None,
        }
        response = await self._client.get(url, params=_params)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return PaginatedSDKAPIKeyListList.model_validate(response.json())


    async def create(self, data: SDKAPIKeyCreateRequest) -> SDKAPIKeyCreate:
        """
        Create a new SDK API key.
        """
        url = "/api/sdk_keys/"
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
        return SDKAPIKeyCreate.model_validate(response.json())


    async def retrieve(self, id: int) -> SDKAPIKeyDetail:
        """
        ViewSet for SDK API key management. Endpoints: - GET /api/sdk_keys/ -
        List user's SDK API keys - POST /api/sdk_keys/ - Create a new SDK API
        key - GET /api/sdk_keys/{id}/ - Get SDK API key details - DELETE
        /api/sdk_keys/{id}/ - Deactivate SDK API key - POST
        /api/sdk_keys/{id}/rotate/ - Rotate SDK API key - POST
        /api/sdk_keys/{id}/reactivate/ - Reactivate SDK API key
        """
        url = f"/api/sdk_keys/{id}/"
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
        return SDKAPIKeyDetail.model_validate(response.json())


    async def update(self, id: int) -> SDKAPIKeyList:
        """
        ViewSet for SDK API key management. Endpoints: - GET /api/sdk_keys/ -
        List user's SDK API keys - POST /api/sdk_keys/ - Create a new SDK API
        key - GET /api/sdk_keys/{id}/ - Get SDK API key details - DELETE
        /api/sdk_keys/{id}/ - Deactivate SDK API key - POST
        /api/sdk_keys/{id}/rotate/ - Rotate SDK API key - POST
        /api/sdk_keys/{id}/reactivate/ - Reactivate SDK API key
        """
        url = f"/api/sdk_keys/{id}/"
        response = await self._client.put(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return SDKAPIKeyList.model_validate(response.json())


    async def partial_update(self, id: int) -> SDKAPIKeyList:
        """
        ViewSet for SDK API key management. Endpoints: - GET /api/sdk_keys/ -
        List user's SDK API keys - POST /api/sdk_keys/ - Create a new SDK API
        key - GET /api/sdk_keys/{id}/ - Get SDK API key details - DELETE
        /api/sdk_keys/{id}/ - Deactivate SDK API key - POST
        /api/sdk_keys/{id}/rotate/ - Rotate SDK API key - POST
        /api/sdk_keys/{id}/reactivate/ - Reactivate SDK API key
        """
        url = f"/api/sdk_keys/{id}/"
        response = await self._client.patch(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return SDKAPIKeyList.model_validate(response.json())


    async def destroy(self, id: int) -> None:
        """
        Deactivate an SDK API key (soft delete).
        """
        url = f"/api/sdk_keys/{id}/"
        response = await self._client.delete(url)
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


    async def reactivate_create(self, id: int) -> SDKAPIKeyList:
        """
        Reactivate a deactivated SDK API key.
        """
        url = f"/api/sdk_keys/{id}/reactivate/"
        response = await self._client.post(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return SDKAPIKeyList.model_validate(response.json())


    async def rotate_create(self, id: int) -> SDKAPIKeyList:
        """
        Rotate an SDK API key (generate new key).
        """
        url = f"/api/sdk_keys/{id}/rotate/"
        response = await self._client.post(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return SDKAPIKeyList.model_validate(response.json())


