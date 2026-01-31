"""CDN file storage tool using generated API client."""

import logging
import time
import asyncio
from pathlib import Path
from typing import Any, BinaryIO

from .._config import SDKConfig
from ..exceptions import api_error_handler, async_api_error_handler

logger = logging.getLogger(__name__)
from .._api.client import (
    BaseResource,
    AsyncBaseResource,
    SyncCdnCdnAPI,
    CdnCdnAPI,
)
from .._api.generated.cdn.cdn__api__cdn.models import (
    CDNFileList,
    CDNFileDetail,
    CDNFileUploadRequest,
    CDNFileUploadResponse,
    CDNUploadAsyncResponse,
    CDNJobStatus,
    PaginatedCDNFileListList,
    CDNStats,
)


class CDNResource(BaseResource):
    """CDN file storage tool (sync).

    Uses generated SyncCdnCdnAPI client.
    """

    def __init__(self, config: SDKConfig):
        super().__init__(config)
        self._api = SyncCdnCdnAPI(self._http_client)

    @api_error_handler
    def upload(
        self,
        file: Path | BinaryIO | bytes | None = None,
        *,
        url: str | None = None,
        filename: str | None = None,
        ttl: str | None = None,
        is_public: bool = True,
        metadata: dict[str, Any] | None = None,
        wait: bool = True,
        poll_interval: float = 1.0,
        timeout: float = 120.0,
    ) -> CDNFileUploadResponse:
        """
        Upload a file to CDN.

        Supports two modes:
        - file: Direct upload from Path, bytes, or file-like object
        - url: Server downloads from URL (automatically waits for completion)

        Args:
            file: File to upload (Path, bytes, or file-like object)
            url: URL to download from (alternative to file)
            filename: Override filename
            ttl: Time to live (e.g., "7d", "24h")
            is_public: Whether file is publicly accessible
            metadata: Additional metadata
            wait: If True (default), wait for URL downloads to complete
            poll_interval: Seconds between status checks
            timeout: Maximum seconds to wait for completion

        Returns:
            CDNFileUploadResponse with file details
        """
        if not file and not url:
            logger.error("CDN upload failed: neither file nor url provided")
            raise ValueError("Either 'file' or 'url' must be provided")
        if file and url:
            logger.error("CDN upload failed: both file and url provided")
            raise ValueError("Provide either 'file' or 'url', not both")

        # Prepare file data if provided
        file_tuple = None
        if file:
            if isinstance(file, Path):
                filename = filename or file.name
                logger.debug("CDN upload from file: %s", file)
                with open(file, "rb") as f:
                    content = f.read()
                file_tuple = (filename, content)
            elif isinstance(file, bytes):
                if not filename:
                    logger.error("CDN upload failed: filename required for bytes")
                    raise ValueError("filename required when uploading bytes")
                file_tuple = (filename, file)
            else:
                # BinaryIO
                content = file.read()
                filename = filename or getattr(file, "name", "file")
                file_tuple = (filename, content)

            logger.debug("CDN uploading file: %s", filename)

        # Build request using generated model
        request = CDNFileUploadRequest(
            file=file_tuple,
            url=url,
            filename=filename if url else None,  # Only for URL mode
            ttl=ttl,
            is_public=is_public,
            metadata=metadata,
        )

        result = self._api.create(request)

        # Direct upload - return immediately
        if isinstance(result, CDNFileUploadResponse):
            logger.info("CDN upload completed: uuid=%s", result.uuid)
            return result

        # Async upload (URL mode) - poll for completion if wait=True
        logger.info("CDN upload started async job: %s", result.job_id)

        if not wait:
            # Return file response from job result when available
            raise RuntimeError(
                f"Async upload started (job_id={result.job_id}). "
                "Use wait=True to wait for completion."
            )

        return self._wait_for_job(
            job_id=result.job_id,
            poll_interval=poll_interval,
            timeout=timeout,
        )

    def _wait_for_job(
        self,
        job_id: str,
        poll_interval: float,
        timeout: float,
    ) -> CDNFileUploadResponse:
        """Poll job status until completion."""
        start_time = time.time()

        while True:
            status = self._api.jobs_retrieve(job_id)
            logger.debug("CDN job %s status: %s", job_id, status.status)

            if status.status == "finished":
                if status.result:
                    # Result contains the file data
                    return CDNFileUploadResponse.model_validate(status.result)
                raise RuntimeError(f"Job {job_id} finished but no result returned")

            if status.status == "failed":
                raise RuntimeError(f"CDN upload failed: {status.error or 'Unknown error'}")

            elapsed = time.time() - start_time
            if elapsed >= timeout:
                raise TimeoutError(
                    f"CDN upload job {job_id} did not complete within {timeout}s"
                )

            time.sleep(poll_interval)

    @api_error_handler
    def job_status(self, job_id: str) -> CDNJobStatus:
        """Get status of a background upload job."""
        return self._api.jobs_retrieve(job_id)

    @api_error_handler
    def get(self, uuid: str) -> CDNFileDetail:
        """Get file details by UUID."""
        return self._api.retrieve(uuid)

    @api_error_handler
    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedCDNFileListList:
        """List files."""
        return self._api.list(page=page, page_size=page_size)  # type: ignore[return-value]

    @api_error_handler
    def delete(self, uuid: str) -> bool:
        """Delete a file by UUID."""
        logger.debug("CDN deleting file: %s", uuid)
        self._api.destroy(uuid)
        logger.info("CDN file deleted: %s", uuid)
        return True

    @api_error_handler
    def stats(self) -> CDNStats:
        """Get storage statistics."""
        return self._api.stats_retrieve()


class AsyncCDNResource(AsyncBaseResource):
    """CDN file storage tool (async).

    Uses generated CdnCdnAPI client.
    """

    def __init__(self, config: SDKConfig):
        super().__init__(config)
        self._api = CdnCdnAPI(self._http_client)

    @async_api_error_handler
    async def upload(
        self,
        file: Path | BinaryIO | bytes | None = None,
        *,
        url: str | None = None,
        filename: str | None = None,
        ttl: str | None = None,
        is_public: bool = True,
        metadata: dict[str, Any] | None = None,
        wait: bool = True,
        poll_interval: float = 1.0,
        timeout: float = 120.0,
    ) -> CDNFileUploadResponse:
        """
        Upload a file to CDN.

        Supports two modes:
        - file: Direct upload from Path, bytes, or file-like object
        - url: Server downloads from URL (automatically waits for completion)

        Args:
            file: File to upload (Path, bytes, or file-like object)
            url: URL to download from (alternative to file)
            filename: Override filename
            ttl: Time to live (e.g., "7d", "24h")
            is_public: Whether file is publicly accessible
            metadata: Additional metadata
            wait: If True (default), wait for URL downloads to complete
            poll_interval: Seconds between status checks
            timeout: Maximum seconds to wait for completion

        Returns:
            CDNFileUploadResponse with file details
        """
        if not file and not url:
            logger.error("CDN upload failed: neither file nor url provided")
            raise ValueError("Either 'file' or 'url' must be provided")
        if file and url:
            logger.error("CDN upload failed: both file and url provided")
            raise ValueError("Provide either 'file' or 'url', not both")

        # Prepare file data if provided
        file_tuple = None
        if file:
            if isinstance(file, Path):
                filename = filename or file.name
                logger.debug("CDN async upload from file: %s", file)
                with open(file, "rb") as f:
                    content = f.read()
                file_tuple = (filename, content)
            elif isinstance(file, bytes):
                if not filename:
                    logger.error("CDN upload failed: filename required for bytes")
                    raise ValueError("filename required when uploading bytes")
                file_tuple = (filename, file)
            else:
                # BinaryIO
                content = file.read()
                filename = filename or getattr(file, "name", "file")
                file_tuple = (filename, content)

            logger.debug("CDN async uploading file: %s", filename)

        # Build request using generated model
        request = CDNFileUploadRequest(
            file=file_tuple,
            url=url,
            filename=filename if url else None,  # Only for URL mode
            ttl=ttl,
            is_public=is_public,
            metadata=metadata,
        )

        result = await self._api.create(request)

        # Direct upload - return immediately
        if isinstance(result, CDNFileUploadResponse):
            logger.info("CDN async upload completed: uuid=%s", result.uuid)
            return result

        # Async upload (URL mode) - poll for completion if wait=True
        logger.info("CDN async upload started async job: %s", result.job_id)

        if not wait:
            raise RuntimeError(
                f"Async upload started (job_id={result.job_id}). "
                "Use wait=True to wait for completion."
            )

        return await self._wait_for_job(
            job_id=result.job_id,
            poll_interval=poll_interval,
            timeout=timeout,
        )

    async def _wait_for_job(
        self,
        job_id: str,
        poll_interval: float,
        timeout: float,
    ) -> CDNFileUploadResponse:
        """Poll job status until completion."""
        start_time = time.time()

        while True:
            status = await self._api.jobs_retrieve(job_id)
            logger.debug("CDN job %s status: %s", job_id, status.status)

            if status.status == "finished":
                if status.result:
                    return CDNFileUploadResponse.model_validate(status.result)
                raise RuntimeError(f"Job {job_id} finished but no result returned")

            if status.status == "failed":
                raise RuntimeError(f"CDN upload failed: {status.error or 'Unknown error'}")

            elapsed = time.time() - start_time
            if elapsed >= timeout:
                raise TimeoutError(
                    f"CDN upload job {job_id} did not complete within {timeout}s"
                )

            await asyncio.sleep(poll_interval)

    @async_api_error_handler
    async def job_status(self, job_id: str) -> CDNJobStatus:
        """Get status of a background upload job."""
        return await self._api.jobs_retrieve(job_id)

    @async_api_error_handler
    async def get(self, uuid: str) -> CDNFileDetail:
        """Get file details by UUID."""
        return await self._api.retrieve(uuid)

    @async_api_error_handler
    async def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedCDNFileListList:
        """List files."""
        return await self._api.list(page=page, page_size=page_size)  # type: ignore[return-value]

    @async_api_error_handler
    async def delete(self, uuid: str) -> bool:
        """Delete a file by UUID."""
        logger.debug("CDN async deleting file: %s", uuid)
        await self._api.destroy(uuid)
        logger.info("CDN file deleted: %s", uuid)
        return True

    @async_api_error_handler
    async def stats(self) -> CDNStats:
        """Get storage statistics."""
        return await self._api.stats_retrieve()


__all__ = [
    "CDNResource",
    "AsyncCDNResource",
    "CDNStats",
    # Models
    "CDNFileList",
    "CDNFileDetail",
    "CDNFileUploadRequest",
    "CDNFileUploadResponse",
    "CDNUploadAsyncResponse",
    "CDNJobStatus",
    "PaginatedCDNFileListList",
]
