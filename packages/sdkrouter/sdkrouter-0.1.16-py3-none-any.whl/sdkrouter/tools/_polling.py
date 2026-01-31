"""Common polling logic for async job resources."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Awaitable, Callable, Literal, TypeVar

T = TypeVar("T")
StatusT = TypeVar("StatusT")

JobStatusType = Literal["queued", "pending", "processing", "success", "error"]

logger = logging.getLogger(__name__)


class PollingMixin:
    """Mixin providing sync polling functionality."""

    def _poll_until_complete(
        self,
        job_uuid: str,
        get_status: Callable[[], StatusT],
        get_result: Callable[[], T],
        status_attr: str = "status",
        error_attr: str = "error",
        success_status: JobStatusType = "success",
        error_status: JobStatusType = "error",
        poll_interval: float = 2.0,
        timeout: float = 300.0,
        error_message: str = "Job failed",
    ) -> T:
        """
        Poll job status until completion.

        Args:
            job_uuid: Job UUID for logging
            get_status: Callable returning status object
            get_result: Callable returning final result
            status_attr: Attribute name on status object containing status string
            error_attr: Attribute name on status object containing error details
            success_status: Status value indicating success
            error_status: Status value indicating error
            poll_interval: Seconds between status checks
            timeout: Maximum seconds to wait
            error_message: Error message prefix on failure

        Returns:
            Result from get_result() on success

        Raises:
            TimeoutError: If timeout exceeded
            RuntimeError: If job fails
        """
        start_time = time.time()

        while True:
            status = get_status()
            current_status = getattr(status, status_attr)

            logger.debug("Job %s status: %s", job_uuid, current_status)

            if current_status == success_status:
                return get_result()

            if current_status == error_status:
                error_detail = getattr(status, error_attr, "Unknown error")
                raise RuntimeError(f"{error_message}: {error_detail}")

            elapsed = time.time() - start_time
            if elapsed >= timeout:
                raise TimeoutError(
                    f"Job {job_uuid} did not complete within {timeout}s (status: {current_status})"
                )

            time.sleep(poll_interval)


class AsyncPollingMixin:
    """Mixin providing async polling functionality."""

    async def _poll_until_complete(
        self,
        job_uuid: str,
        get_status: Callable[[], Awaitable[StatusT]],
        get_result: Callable[[], Awaitable[T]],
        status_attr: str = "status",
        error_attr: str = "error",
        success_status: JobStatusType = "success",
        error_status: JobStatusType = "error",
        poll_interval: float = 2.0,
        timeout: float = 300.0,
        error_message: str = "Job failed",
    ) -> T:
        """
        Async poll job status until completion.

        Args:
            job_uuid: Job UUID for logging
            get_status: Async callable returning status object
            get_result: Async callable returning final result
            status_attr: Attribute name on status object containing status string
            error_attr: Attribute name on status object containing error details
            success_status: Status value indicating success
            error_status: Status value indicating error
            poll_interval: Seconds between status checks
            timeout: Maximum seconds to wait
            error_message: Error message prefix on failure

        Returns:
            Result from get_result() on success

        Raises:
            TimeoutError: If timeout exceeded
            RuntimeError: If job fails
        """
        start_time = time.time()

        while True:
            status = await get_status()
            current_status = getattr(status, status_attr)

            logger.debug("Job %s status: %s", job_uuid, current_status)

            if current_status == success_status:
                return await get_result()

            if current_status == error_status:
                error_detail = getattr(status, error_attr, "Unknown error")
                raise RuntimeError(f"{error_message}: {error_detail}")

            elapsed = time.time() - start_time
            if elapsed >= timeout:
                raise TimeoutError(
                    f"Job {job_uuid} did not complete within {timeout}s (status: {current_status})"
                )

            await asyncio.sleep(poll_interval)


__all__ = ["PollingMixin", "AsyncPollingMixin"]
