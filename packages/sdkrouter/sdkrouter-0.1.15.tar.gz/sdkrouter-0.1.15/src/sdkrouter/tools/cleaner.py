"""HTML Cleaner tool using generated API client."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal, overload

from .._config import SDKConfig
from ._polling import PollingMixin, AsyncPollingMixin
from ..exceptions import api_error_handler, async_api_error_handler

logger = logging.getLogger(__name__)
from .._api.client import (
    BaseResource,
    AsyncBaseResource,
    SyncCleanerCleanerAPI,
    CleanerCleanerAPI,
)
from .._api.generated.cleaner.cleaner__api__cleaner.models import (
    CleanRequestRequest,
    CleanAsyncRequestRequest,
    CleanResponse,
    CleaningRequestDetail,
    CleaningStats,
    CleanAsyncResponse,
    JobStatus,
    PatternsResponse,
)
from .._api.generated.cleaner.enums import (
    CleanRequestRequestOutputFormat,
    CleanAsyncRequestRequestOutputFormat,
    CleaningRequestDetailStatus,
)


class CleanerResource(PollingMixin, BaseResource):
    """HTML Cleaner tool (sync).

    Uses generated SyncCleanerCleanerAPI client.
    """

    def __init__(self, config: SDKConfig):
        super().__init__(config)
        self._api = SyncCleanerCleanerAPI(self._http_client)

    @api_error_handler
    def clean(
        self,
        html: bytes | str,
        *,
        filename: str = "input.html",
        output_format: CleanRequestRequestOutputFormat | str = CleanRequestRequestOutputFormat.HTML,
        max_tokens: int = 10000,
        remove_scripts: bool = True,
        remove_styles: bool = True,
        remove_comments: bool = True,
        remove_hidden: bool = True,
        filter_classes: bool = True,
        class_threshold: float = 0.3,
        try_hydration: bool = True,
        preserve_selectors: list[str] | None = None,
    ) -> CleanResponse:
        """Clean HTML content via API using generated client."""
        if isinstance(html, str):
            content = html.encode("utf-8")
        else:
            content = html

        logger.debug(
            "Cleaner processing: %s (%d bytes), format=%s, max_tokens=%d",
            filename,
            len(content),
            output_format,
            max_tokens,
        )

        # Handle string or enum for output_format
        format_value = output_format if isinstance(output_format, CleanRequestRequestOutputFormat) else CleanRequestRequestOutputFormat(output_format)

        # Build request using generated model - file is tuple (filename, content, content_type)
        request = CleanRequestRequest(
            file=(filename, content, "text/html"),
            output_format=format_value,
            max_tokens=max_tokens,
            remove_scripts=remove_scripts,
            remove_styles=remove_styles,
            remove_comments=remove_comments,
            remove_hidden=remove_hidden,
            filter_classes=filter_classes,
            class_threshold=class_threshold,
            try_hydration=try_hydration,
            preserve_selectors=preserve_selectors,
        )

        result = self._api.clean_create(request)
        logger.info(
            "Cleaner completed: %d -> %d bytes (%.1fx compression)",
            result.original_size or len(content),
            result.cleaned_size or 0,
            result.compression_ratio or 1.0,
        )
        return result

    def clean_file(self, file_path: str | Path, **kwargs) -> CleanResponse:
        """Clean HTML file."""
        path = Path(file_path)
        logger.debug("Cleaner reading file: %s", path)
        content = path.read_bytes()
        filename = kwargs.pop("filename", path.name)
        return self.clean(content, filename=filename, **kwargs)

    @api_error_handler
    def get(self, uuid: str) -> CleaningRequestDetail:
        """Get cleaning request details."""
        return self._api.retrieve(uuid)

    @api_error_handler
    def list(self):
        """List cleaning requests."""
        return self._api.list()

    @api_error_handler
    def stats(self) -> CleaningStats:
        """Get cleaning statistics."""
        return self._api.stats_retrieve()

    @overload
    def clean_async(
        self,
        html: bytes | str,
        *,
        wait: Literal[False] = False,
        filename: str = "input.html",
        url: str | None = None,
        task_prompt: str | None = None,
        output_format: CleanAsyncRequestRequestOutputFormat | str = CleanAsyncRequestRequestOutputFormat.HTML,
        config: dict | None = None,
    ) -> CleanAsyncResponse: ...

    @overload
    def clean_async(
        self,
        html: bytes | str,
        *,
        wait: Literal[True],
        poll_interval: float = 2.0,
        timeout: float = 600.0,
        filename: str = "input.html",
        url: str | None = None,
        task_prompt: str | None = None,
        output_format: CleanAsyncRequestRequestOutputFormat | str = CleanAsyncRequestRequestOutputFormat.HTML,
        config: dict | None = None,
    ) -> CleaningRequestDetail: ...

    @api_error_handler
    def clean_async(
        self,
        html: bytes | str,
        *,
        wait: bool = False,
        poll_interval: float = 2.0,
        timeout: float = 600.0,
        filename: str = "input.html",
        url: str | None = None,
        task_prompt: str | None = None,
        output_format: CleanAsyncRequestRequestOutputFormat | str = CleanAsyncRequestRequestOutputFormat.HTML,
        config: dict | None = None,
    ) -> CleanAsyncResponse | CleaningRequestDetail:
        """
        Clean HTML using agent service (async with job queue).

        Args:
            html: HTML content to clean
            wait: If True, poll until completion and return results.
                  If False, return job info immediately.
            poll_interval: Seconds between status checks (only if wait=True)
            timeout: Maximum wait time in seconds (only if wait=True)
            filename: Filename for the content
            url: Source URL for context
            task_prompt: Custom instructions for the agent
            output_format: Output format (html, markdown)
            config: Additional configuration dict

        Returns:
            If wait=False: CleanAsyncResponse with job_id, request_uuid
            If wait=True: CleaningRequestDetail with cleaned_html and patterns

        Raises:
            TimeoutError: If wait=True and job doesn't complete within timeout
            RuntimeError: If wait=True and job fails with error
        """
        content = html if isinstance(html, bytes) else html.encode("utf-8")
        format_value = output_format if isinstance(output_format, CleanAsyncRequestRequestOutputFormat) else CleanAsyncRequestRequestOutputFormat(output_format)

        logger.debug("Cleaner async processing: %s (%d bytes, wait=%s)", filename, len(content), wait)

        # Build request using generated model
        request = CleanAsyncRequestRequest(
            file=(filename, content, "text/html"),
            url=url,
            task_prompt=task_prompt,
            output_format=format_value,
            config=config if config else None,
        )

        job = self._api.clean_async_create(request)
        logger.info("Cleaner async job queued: %s (status=%s)", job.request_uuid, job.status)

        if not wait:
            return job

        return self._poll_until_complete(
            job_uuid=job.request_uuid,
            get_status=lambda: self.job_status(job.request_uuid),
            get_result=lambda: self.get(job.request_uuid),
            error_message="Clean job failed",
            poll_interval=poll_interval,
            timeout=timeout,
        )

    @api_error_handler
    def job_status(self, uuid: str) -> JobStatus:
        """
        Get status of async cleaning job.

        Args:
            uuid: Request UUID from clean_async()

        Returns:
            JobStatus with status, timestamps, duration
        """
        return self._api.status_retrieve(uuid)

    @api_error_handler
    def patterns(self, uuid: str) -> PatternsResponse:
        """
        Get extraction patterns from completed async clean.

        Args:
            uuid: Request UUID from clean_async()

        Returns:
            PatternsResponse with patterns list and count

        Raises:
            APIError: If job not completed
        """
        return self._api.patterns_retrieve(uuid)


class AsyncCleanerResource(AsyncPollingMixin, AsyncBaseResource):
    """HTML Cleaner tool (async).

    Uses generated CleanerCleanerAPI client.
    """

    def __init__(self, config: SDKConfig):
        super().__init__(config)
        self._api = CleanerCleanerAPI(self._http_client)

    @async_api_error_handler
    async def clean(
        self,
        html: bytes | str,
        *,
        filename: str = "input.html",
        output_format: CleanRequestRequestOutputFormat | str = CleanRequestRequestOutputFormat.HTML,
        max_tokens: int = 10000,
        remove_scripts: bool = True,
        remove_styles: bool = True,
        remove_comments: bool = True,
        remove_hidden: bool = True,
        filter_classes: bool = True,
        class_threshold: float = 0.3,
        try_hydration: bool = True,
        preserve_selectors: list[str] | None = None,
    ) -> CleanResponse:
        """Clean HTML content via API using generated client."""
        if isinstance(html, str):
            content = html.encode("utf-8")
        else:
            content = html

        logger.debug(
            "Cleaner async processing: %s (%d bytes), format=%s, max_tokens=%d",
            filename,
            len(content),
            output_format,
            max_tokens,
        )

        # Handle string or enum for output_format
        format_value = output_format if isinstance(output_format, CleanRequestRequestOutputFormat) else CleanRequestRequestOutputFormat(output_format)

        # Build request using generated model
        request = CleanRequestRequest(
            file=(filename, content, "text/html"),
            output_format=format_value,
            max_tokens=max_tokens,
            remove_scripts=remove_scripts,
            remove_styles=remove_styles,
            remove_comments=remove_comments,
            remove_hidden=remove_hidden,
            filter_classes=filter_classes,
            class_threshold=class_threshold,
            try_hydration=try_hydration,
            preserve_selectors=preserve_selectors,
        )

        result = await self._api.clean_create(request)
        logger.info(
            "Cleaner completed: %d -> %d bytes (%.1fx compression)",
            result.original_size or len(content),
            result.cleaned_size or 0,
            result.compression_ratio or 1.0,
        )
        return result

    async def clean_file(self, file_path: str | Path, **kwargs) -> CleanResponse:
        """Clean HTML file."""
        path = Path(file_path)
        logger.debug("Cleaner async reading file: %s", path)
        content = path.read_bytes()
        filename = kwargs.pop("filename", path.name)
        return await self.clean(content, filename=filename, **kwargs)

    @async_api_error_handler
    async def get(self, uuid: str) -> CleaningRequestDetail:
        """Get cleaning request details."""
        return await self._api.retrieve(uuid)

    @async_api_error_handler
    async def list(self):
        """List cleaning requests."""
        return await self._api.list()

    @async_api_error_handler
    async def stats(self) -> CleaningStats:
        """Get cleaning statistics."""
        return await self._api.stats_retrieve()

    @overload
    async def clean_async(
        self,
        html: bytes | str,
        *,
        wait: Literal[False] = False,
        filename: str = "input.html",
        url: str | None = None,
        task_prompt: str | None = None,
        output_format: CleanAsyncRequestRequestOutputFormat | str = CleanAsyncRequestRequestOutputFormat.HTML,
        config: dict | None = None,
    ) -> CleanAsyncResponse: ...

    @overload
    async def clean_async(
        self,
        html: bytes | str,
        *,
        wait: Literal[True],
        poll_interval: float = 2.0,
        timeout: float = 600.0,
        filename: str = "input.html",
        url: str | None = None,
        task_prompt: str | None = None,
        output_format: CleanAsyncRequestRequestOutputFormat | str = CleanAsyncRequestRequestOutputFormat.HTML,
        config: dict | None = None,
    ) -> CleaningRequestDetail: ...

    @async_api_error_handler
    async def clean_async(
        self,
        html: bytes | str,
        *,
        wait: bool = False,
        poll_interval: float = 2.0,
        timeout: float = 600.0,
        filename: str = "input.html",
        url: str | None = None,
        task_prompt: str | None = None,
        output_format: CleanAsyncRequestRequestOutputFormat | str = CleanAsyncRequestRequestOutputFormat.HTML,
        config: dict | None = None,
    ) -> CleanAsyncResponse | CleaningRequestDetail:
        """
        Clean HTML using agent service (async with job queue).

        Args:
            html: HTML content to clean
            wait: If True, poll until completion and return results.
                  If False, return job info immediately.
            poll_interval: Seconds between status checks (only if wait=True)
            timeout: Maximum wait time in seconds (only if wait=True)
            filename: Filename for the content
            url: Source URL for context
            task_prompt: Custom instructions for the agent
            output_format: Output format (html, markdown)
            config: Additional configuration dict

        Returns:
            If wait=False: CleanAsyncResponse with job_id, request_uuid
            If wait=True: CleaningRequestDetail with cleaned_html and patterns

        Raises:
            TimeoutError: If wait=True and job doesn't complete within timeout
            RuntimeError: If wait=True and job fails with error
        """
        content = html if isinstance(html, bytes) else html.encode("utf-8")
        format_value = output_format if isinstance(output_format, CleanAsyncRequestRequestOutputFormat) else CleanAsyncRequestRequestOutputFormat(output_format)

        logger.debug("Cleaner async processing: %s (%d bytes, wait=%s)", filename, len(content), wait)

        # Build request using generated model
        request = CleanAsyncRequestRequest(
            file=(filename, content, "text/html"),
            url=url,
            task_prompt=task_prompt,
            output_format=format_value,
            config=config if config else None,
        )

        job = await self._api.clean_async_create(request)
        logger.info("Cleaner async job queued: %s (status=%s)", job.request_uuid, job.status)

        if not wait:
            return job

        return await self._poll_until_complete(
            job_uuid=job.request_uuid,
            get_status=lambda: self.job_status(job.request_uuid),
            get_result=lambda: self.get(job.request_uuid),
            error_message="Clean job failed",
            poll_interval=poll_interval,
            timeout=timeout,
        )

    @async_api_error_handler
    async def job_status(self, uuid: str) -> JobStatus:
        """
        Get status of async cleaning job.

        Args:
            uuid: Request UUID from clean_async()

        Returns:
            JobStatus with status, timestamps, duration
        """
        return await self._api.status_retrieve(uuid)

    @async_api_error_handler
    async def patterns(self, uuid: str) -> PatternsResponse:
        """
        Get extraction patterns from completed async clean.

        Args:
            uuid: Request UUID from clean_async()

        Returns:
            PatternsResponse with patterns list and count

        Raises:
            APIError: If job not completed
        """
        return await self._api.patterns_retrieve(uuid)


__all__ = [
    "CleanerResource",
    "AsyncCleanerResource",
    # Models
    "CleanRequestRequest",
    "CleanResponse",
    "CleaningRequestDetail",
    "CleaningStats",
    # Async job models
    "CleanAsyncResponse",
    "JobStatus",
    "PatternsResponse",
    # Enums
    "CleanRequestRequestOutputFormat",
    "CleanAsyncRequestRequestOutputFormat",
    "CleaningRequestDetailStatus",
]
