from __future__ import annotations

import httpx

from .models import (
    CleanAsyncRequestRequest,
    CleanAsyncResponse,
    CleanRequestRequest,
    CleanResponse,
    CleaningRequestDetail,
    CleaningStats,
    JobStatus,
    PaginatedCleaningRequestListList,
    PatternsResponse,
)


class CleanerCleanerAPI:
    """API endpoints for Cleaner."""

    def __init__(self, client: httpx.AsyncClient):
        """Initialize sub-client with shared httpx client."""
        self._client = client

    async def list(
        self,
        ordering: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        search: str | None = None,
    ) -> list[PaginatedCleaningRequestListList]:
        """
        List cleaning requests

        List user's cleaning requests.
        """
        url = "/api/cleaner/"
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
        return PaginatedCleaningRequestListList.model_validate(response.json())


    async def retrieve(self, uuid: str) -> CleaningRequestDetail:
        """
        Get cleaning request details

        Get cleaning request details.
        """
        url = f"/api/cleaner/{uuid}/"
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
        return CleaningRequestDetail.model_validate(response.json())


    async def cancel_create(self, uuid: str) -> None:
        """
        Cancel async cleaning job

        Cancel a queued or running cleaning job.
        """
        url = f"/api/cleaner/{uuid}/cancel/"
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
        return None


    async def patterns_retrieve(self, uuid: str) -> PatternsResponse:
        """
        Get extraction patterns

        Get reusable extraction patterns from completed job.
        """
        url = f"/api/cleaner/{uuid}/patterns/"
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
        return PatternsResponse.model_validate(response.json())


    async def status_retrieve(self, uuid: str) -> JobStatus:
        """
        Get job status

        Get status of async cleaning job.
        """
        url = f"/api/cleaner/{uuid}/status/"
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
        return JobStatus.model_validate(response.json())


    async def clean_create(self, data: CleanRequestRequest) -> CleanResponse:
        """
        Clean HTML file

        Clean HTML file. Accepts multipart/form-data with HTML file. Returns
        cleaned HTML with statistics.
        """
        url = "/api/cleaner/clean/"
        # Build multipart form data
        _files = {}
        _form_data = {}
        _raw_data = data.model_dump(exclude_unset=True)
        if 'file' in _raw_data and _raw_data['file'] is not None:
            _files['file'] = _raw_data['file']
        import json as _json
        if 'output_format' in _raw_data and _raw_data['output_format'] is not None:
            _val = _raw_data['output_format']
            _form_data['output_format'] = _val.value if hasattr(_val, 'value') else _val
        if 'max_tokens' in _raw_data and _raw_data['max_tokens'] is not None:
            _form_data['max_tokens'] = _raw_data['max_tokens']
        if 'remove_scripts' in _raw_data and _raw_data['remove_scripts'] is not None:
            _form_data['remove_scripts'] = str(_raw_data['remove_scripts']).lower()
        if 'remove_styles' in _raw_data and _raw_data['remove_styles'] is not None:
            _form_data['remove_styles'] = str(_raw_data['remove_styles']).lower()
        if 'remove_comments' in _raw_data and _raw_data['remove_comments'] is not None:
            _form_data['remove_comments'] = str(_raw_data['remove_comments']).lower()
        if 'remove_hidden' in _raw_data and _raw_data['remove_hidden'] is not None:
            _form_data['remove_hidden'] = str(_raw_data['remove_hidden']).lower()
        if 'filter_classes' in _raw_data and _raw_data['filter_classes'] is not None:
            _form_data['filter_classes'] = str(_raw_data['filter_classes']).lower()
        if 'class_threshold' in _raw_data and _raw_data['class_threshold'] is not None:
            _form_data['class_threshold'] = _raw_data['class_threshold']
        if 'try_hydration' in _raw_data and _raw_data['try_hydration'] is not None:
            _form_data['try_hydration'] = str(_raw_data['try_hydration']).lower()
        if 'preserve_selectors' in _raw_data and _raw_data['preserve_selectors'] is not None:
            _form_data['preserve_selectors'] = _json.dumps(_raw_data['preserve_selectors'])
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
        return CleanResponse.model_validate(response.json())


    async def clean_async_create(self, data: CleanAsyncRequestRequest) -> CleanAsyncResponse:
        """
        Clean HTML async (agent)

        Queue HTML cleaning using agent service. Returns job ID for status
        polling.
        """
        url = "/api/cleaner/clean-async/"
        # Build multipart form data
        _files = {}
        _form_data = {}
        _raw_data = data.model_dump(exclude_unset=True)
        if 'file' in _raw_data and _raw_data['file'] is not None:
            _files['file'] = _raw_data['file']
        import json as _json
        if 'url' in _raw_data and _raw_data['url'] is not None:
            _form_data['url'] = _raw_data['url']
        if 'task_prompt' in _raw_data and _raw_data['task_prompt'] is not None:
            _form_data['task_prompt'] = _raw_data['task_prompt']
        if 'output_format' in _raw_data and _raw_data['output_format'] is not None:
            _val = _raw_data['output_format']
            _form_data['output_format'] = _val.value if hasattr(_val, 'value') else _val
        if 'config' in _raw_data and _raw_data['config'] is not None:
            _form_data['config'] = _json.dumps(_raw_data['config'])
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
        return CleanAsyncResponse.model_validate(response.json())


    async def stats_retrieve(self) -> CleaningStats:
        """
        Get cleaning statistics

        Get cleaning statistics for the current API key.
        """
        url = "/api/cleaner/stats/"
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
        return CleaningStats.model_validate(response.json())


