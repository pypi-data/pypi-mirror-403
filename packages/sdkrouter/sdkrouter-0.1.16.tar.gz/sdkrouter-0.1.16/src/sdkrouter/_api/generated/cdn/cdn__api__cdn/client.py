from __future__ import annotations

import httpx

from .models import (
    CDNFileDetail,
    CDNFileList,
    CDNFileUploadRequest,
    CDNFileUploadResponse,
    CDNJobStatus,
    CDNStats,
    CDNUploadAsyncResponse,
    PaginatedCDNFileListList,
)


class CdnCdnAPI:
    """API endpoints for Cdn."""

    def __init__(self, client: httpx.AsyncClient):
        """Initialize sub-client with shared httpx client."""
        self._client = client

    async def list(
        self,
        ordering: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        search: str | None = None,
    ) -> list[PaginatedCDNFileListList]:
        """
        ViewSet for CDN file management. Endpoints: - GET /api/cdn/ - List
        user's files - POST /api/cdn/ - Upload a new file - GET /api/cdn/{uuid}/
        - Get file details - DELETE /api/cdn/{uuid}/ - Delete file - GET
        /api/cdn/stats/ - Get storage statistics
        """
        url = "/api/cdn/"
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
        return PaginatedCDNFileListList.model_validate(response.json())


    async def create(
        self,
        data: CDNFileUploadRequest,
    ) -> CDNFileUploadResponse | CDNUploadAsyncResponse:
        """
        Upload file

        Upload a new file (multipart) or download from URL. For direct file
        uploads, returns 201 with file data. For URL downloads via background
        job, returns 202 with job info.
        """
        url = "/api/cdn/"
        # Build multipart form data
        _files = {}
        _form_data = {}
        _raw_data = data.model_dump(exclude_unset=True)
        if 'file' in _raw_data and _raw_data['file'] is not None:
            _files['file'] = _raw_data['file']
        import json as _json
        if 'url' in _raw_data and _raw_data['url'] is not None:
            _form_data['url'] = _raw_data['url']
        if 'filename' in _raw_data and _raw_data['filename'] is not None:
            _form_data['filename'] = _raw_data['filename']
        if 'ttl' in _raw_data and _raw_data['ttl'] is not None:
            _form_data['ttl'] = _raw_data['ttl']
        if 'is_public' in _raw_data and _raw_data['is_public'] is not None:
            _form_data['is_public'] = str(_raw_data['is_public']).lower()
        if 'metadata' in _raw_data and _raw_data['metadata'] is not None:
            _form_data['metadata'] = _json.dumps(_raw_data['metadata'])
        response = await self._client.post(url, files=_files if _files else None, data=_form_data if _form_data else None)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        if response.status_code == 201:
            return CDNFileUploadResponse.model_validate(response.json())
        elif response.status_code == 202:
            return CDNUploadAsyncResponse.model_validate(response.json())
        else:
            return CDNFileUploadResponse.model_validate(response.json())


    async def retrieve(self, uuid: str) -> CDNFileDetail:
        """
        ViewSet for CDN file management. Endpoints: - GET /api/cdn/ - List
        user's files - POST /api/cdn/ - Upload a new file - GET /api/cdn/{uuid}/
        - Get file details - DELETE /api/cdn/{uuid}/ - Delete file - GET
        /api/cdn/stats/ - Get storage statistics
        """
        url = f"/api/cdn/{uuid}/"
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
        return CDNFileDetail.model_validate(response.json())


    async def update(self, uuid: str) -> CDNFileList:
        """
        ViewSet for CDN file management. Endpoints: - GET /api/cdn/ - List
        user's files - POST /api/cdn/ - Upload a new file - GET /api/cdn/{uuid}/
        - Get file details - DELETE /api/cdn/{uuid}/ - Delete file - GET
        /api/cdn/stats/ - Get storage statistics
        """
        url = f"/api/cdn/{uuid}/"
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
        return CDNFileList.model_validate(response.json())


    async def partial_update(self, uuid: str) -> CDNFileList:
        """
        ViewSet for CDN file management. Endpoints: - GET /api/cdn/ - List
        user's files - POST /api/cdn/ - Upload a new file - GET /api/cdn/{uuid}/
        - Get file details - DELETE /api/cdn/{uuid}/ - Delete file - GET
        /api/cdn/stats/ - Get storage statistics
        """
        url = f"/api/cdn/{uuid}/"
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
        return CDNFileList.model_validate(response.json())


    async def destroy(self, uuid: str) -> None:
        """
        Delete a file.
        """
        url = f"/api/cdn/{uuid}/"
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


    async def jobs_retrieve(self, job_id: str) -> CDNJobStatus:
        """
        Get job status

        Get status of background file download job.
        """
        url = f"/api/cdn/jobs/{job_id}/"
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
        return CDNJobStatus.model_validate(response.json())


    async def stats_retrieve(self) -> CDNStats:
        """
        Get storage statistics

        Get CDN storage statistics for the current user.
        """
        url = "/api/cdn/stats/"
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
        return CDNStats.model_validate(response.json())


