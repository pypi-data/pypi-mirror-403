"""Image generation tool using generated API client.

Provides both synchronous and asynchronous image generation
with support for model aliases, quality/style options, and
async job polling.

Example:
    from sdkrouter import SDKRouter

    client = SDKRouter(api_key="...")

    # Sync generation
    result = client.image_gen.generate(
        prompt="A sunset over mountains",
        model="@balanced",
        size="1024x1024",
    )
    print(f"Image URL: {result.image_cdn_url}")

    # Async generation with polling
    job = client.image_gen.generate_async(prompt="...")
    result = client.image_gen.wait_for_completion(job.id)
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

from .._api.client import (
    BaseResource,
    AsyncBaseResource,
)
from .._api.generated.image_gen.image_gen__api__image_gen.sync_client import (
    SyncImageGenImageGenAPI,
)
from .._api.generated.image_gen.image_gen__api__image_gen.client import (
    ImageGenImageGenAPI,
)
from .._api.generated.image_gen.image_gen__api__image_gen.models import (
    ImageGenerateRequestRequest,
    ImageGenerateResponse,
    AsyncGenerateResponse,
    JobStatus,
    ImageGenerationList,
    ImageGenerationDetail,
    ImageGenOptions,
    ChoiceItem,
)
from .._api.generated.image_gen.enums import (
    ImageGenerateRequestRequestQuality,
    ImageGenerateRequestRequestStyle,
    ImageGenerateResponseStatus,
)
from ..exceptions import api_error_handler, async_api_error_handler, APIError

if TYPE_CHECKING:
    from .._config import SDKConfig

logger = logging.getLogger(__name__)


class ImageGenResource(BaseResource):
    """Image generation tool (sync).

    Uses generated SyncImageGenImageGenAPI client.

    Example:
        result = client.image_gen.generate(
            prompt="A beautiful sunset",
            model="@balanced",
            quality="hd",
        )
        print(f"Generated: {result.image_cdn_url}")
    """

    def __init__(self, config: "SDKConfig"):
        super().__init__(config)
        self._api = SyncImageGenImageGenAPI(self._http_client)

    @api_error_handler
    def generate(
        self,
        prompt: str,
        *,
        negative_prompt: str | None = None,
        model: str | None = None,
        size: str | None = None,
        quality: ImageGenerateRequestRequestQuality | str | None = None,
        style: ImageGenerateRequestRequestStyle | str | None = None,
    ) -> ImageGenerateResponse:
        """Generate an image synchronously.

        Args:
            prompt: Text description of the image to generate (max 4000 chars)
            negative_prompt: What to avoid in the image (max 1000 chars)
            model: Model to use. Supports aliases: @cheap, @balanced, @smart, @fast
            size: Image size (e.g., "1024x1024", "1792x1024")
            quality: Quality level ("standard" or "hd")
            style: Style ("natural" or "vivid")

        Returns:
            ImageGenerateResponse with image URLs and metadata

        Raises:
            ValidationError: If request parameters are invalid
            RateLimitError: If rate limit is exceeded
            APIError: For other API errors
        """
        logger.debug("Image generate: prompt=%s, model=%s", prompt[:50], model)

        kwargs: dict = {"prompt": prompt}
        if negative_prompt is not None:
            kwargs["negative_prompt"] = negative_prompt
        if model is not None:
            kwargs["model"] = model
        if size is not None:
            kwargs["size"] = size
        if quality is not None:
            kwargs["quality"] = quality
        if style is not None:
            kwargs["style"] = style

        request = ImageGenerateRequestRequest(**kwargs)
        result = self._api.generate_create(request)

        logger.info(
            "Image generated: id=%s, cost=$%s",
            result.id,
            result.cost_usd or "0",
        )
        return result

    @api_error_handler
    def generate_async(
        self,
        prompt: str,
        *,
        negative_prompt: str | None = None,
        model: str | None = None,
        size: str | None = None,
        quality: ImageGenerateRequestRequestQuality | str | None = None,
        style: ImageGenerateRequestRequestStyle | str | None = None,
    ) -> AsyncGenerateResponse:
        """Start async image generation.

        Returns immediately with a job_id for polling.

        Args:
            prompt: Text description of the image to generate
            negative_prompt: What to avoid in the image
            model: Model to use (supports aliases)
            size: Image size
            quality: Quality level
            style: Style

        Returns:
            AsyncGenerateResponse with id and job_id for polling

        Example:
            job = client.image_gen.generate_async(prompt="...")
            result = client.image_gen.wait_for_completion(job.id)
        """
        logger.debug("Image generate async: prompt=%s", prompt[:50])

        kwargs: dict = {"prompt": prompt}
        if negative_prompt is not None:
            kwargs["negative_prompt"] = negative_prompt
        if model is not None:
            kwargs["model"] = model
        if size is not None:
            kwargs["size"] = size
        if quality is not None:
            kwargs["quality"] = quality
        if style is not None:
            kwargs["style"] = style

        request = ImageGenerateRequestRequest(**kwargs)
        result = self._api.generate_async_create(request)

        logger.info("Image generation queued: id=%s, job_id=%s", result.id, result.job_id)
        return result

    @api_error_handler
    def get_status(self, generation_id: int | str) -> JobStatus:
        """Get status of an async generation job.

        Args:
            generation_id: ID of the generation to check

        Returns:
            JobStatus with current status and image URL if completed
        """
        return self._api.status_retrieve(str(generation_id))

    @api_error_handler
    def get(self, generation_id: int | str) -> ImageGenerationDetail:
        """Get details of a generation.

        Args:
            generation_id: ID of the generation

        Returns:
            Full generation details including all metadata
        """
        return self._api.retrieve(str(generation_id))

    @api_error_handler
    def list(
        self,
        *,
        ordering: str | None = None,
        search: str | None = None,
    ) -> list[ImageGenerationList]:
        """List generation history.

        Args:
            ordering: Field to order by (e.g., "-created_at")
            search: Search query for prompt text

        Returns:
            List of generations
        """
        return self._api.list(ordering=ordering, search=search)

    @api_error_handler
    def options(self) -> ImageGenOptions:
        """Get available generation options.

        Returns:
            Available quality, style, model aliases, and default model
        """
        return self._api.options_retrieve()

    def wait_for_completion(
        self,
        generation_id: int | str,
        *,
        timeout: float = 300.0,
        poll_interval: float = 2.0,
    ) -> ImageGenerationDetail:
        """Wait for async generation to complete.

        Args:
            generation_id: ID of the generation to wait for
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks

        Returns:
            Completed ImageGenerationDetail

        Raises:
            TimeoutError: If generation doesn't complete within timeout
            APIError: If generation fails
        """
        start_time = time.monotonic()

        while True:
            elapsed = time.monotonic() - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"Image generation {generation_id} did not complete within {timeout}s"
                )

            status = self.get_status(generation_id)
            logger.debug(
                "Generation %s status: %s (elapsed: %.1fs)",
                generation_id,
                status.status,
                elapsed,
            )

            if status.status == ImageGenerateResponseStatus.COMPLETED:
                return self.get(generation_id)
            elif status.status in (
                ImageGenerateResponseStatus.FAILED,
                ImageGenerateResponseStatus.CANCELLED,
            ):
                error_msg = status.error or f"Generation {status.status}"
                raise APIError(error_msg)

            time.sleep(poll_interval)


class AsyncImageGenResource(AsyncBaseResource):
    """Image generation tool (async).

    Uses generated ImageGenImageGenAPI client.

    Example:
        result = await client.image_gen.generate(
            prompt="A beautiful sunset",
            model="@balanced",
        )
        print(f"Generated: {result.image_cdn_url}")
    """

    def __init__(self, config: "SDKConfig"):
        super().__init__(config)
        self._api = ImageGenImageGenAPI(self._http_client)

    @async_api_error_handler
    async def generate(
        self,
        prompt: str,
        *,
        negative_prompt: str | None = None,
        model: str | None = None,
        size: str | None = None,
        quality: ImageGenerateRequestRequestQuality | str | None = None,
        style: ImageGenerateRequestRequestStyle | str | None = None,
    ) -> ImageGenerateResponse:
        """Generate an image asynchronously.

        Args:
            prompt: Text description of the image to generate (max 4000 chars)
            negative_prompt: What to avoid in the image (max 1000 chars)
            model: Model to use. Supports aliases: @cheap, @balanced, @smart, @fast
            size: Image size (e.g., "1024x1024", "1792x1024")
            quality: Quality level ("standard" or "hd")
            style: Style ("natural" or "vivid")

        Returns:
            ImageGenerateResponse with image URLs and metadata
        """
        logger.debug("Image generate async: prompt=%s", prompt[:50])

        kwargs: dict = {"prompt": prompt}
        if negative_prompt is not None:
            kwargs["negative_prompt"] = negative_prompt
        if model is not None:
            kwargs["model"] = model
        if size is not None:
            kwargs["size"] = size
        if quality is not None:
            kwargs["quality"] = quality
        if style is not None:
            kwargs["style"] = style

        request = ImageGenerateRequestRequest(**kwargs)
        result = await self._api.generate_create(request)

        logger.info("Image generated: id=%s, cost=$%s", result.id, result.cost_usd or "0")
        return result

    @async_api_error_handler
    async def generate_async(
        self,
        prompt: str,
        *,
        negative_prompt: str | None = None,
        model: str | None = None,
        size: str | None = None,
        quality: ImageGenerateRequestRequestQuality | str | None = None,
        style: ImageGenerateRequestRequestStyle | str | None = None,
    ) -> AsyncGenerateResponse:
        """Start async image generation (returns immediately).

        Args:
            prompt: Text description of the image to generate
            negative_prompt: What to avoid in the image
            model: Model to use (supports aliases)
            size: Image size
            quality: Quality level
            style: Style

        Returns:
            AsyncGenerateResponse with id and job_id for polling
        """
        kwargs: dict = {"prompt": prompt}
        if negative_prompt is not None:
            kwargs["negative_prompt"] = negative_prompt
        if model is not None:
            kwargs["model"] = model
        if size is not None:
            kwargs["size"] = size
        if quality is not None:
            kwargs["quality"] = quality
        if style is not None:
            kwargs["style"] = style

        request = ImageGenerateRequestRequest(**kwargs)
        result = await self._api.generate_async_create(request)

        logger.info("Image generation queued: id=%s, job_id=%s", result.id, result.job_id)
        return result

    @async_api_error_handler
    async def get_status(self, generation_id: int | str) -> JobStatus:
        """Get status of an async generation job.

        Args:
            generation_id: ID of the generation to check

        Returns:
            JobStatus with current status and image URL if completed
        """
        return await self._api.status_retrieve(str(generation_id))

    @async_api_error_handler
    async def get(self, generation_id: int | str) -> ImageGenerationDetail:
        """Get details of a generation.

        Args:
            generation_id: ID of the generation

        Returns:
            Full generation details including all metadata
        """
        return await self._api.retrieve(str(generation_id))

    @async_api_error_handler
    async def list(
        self,
        *,
        ordering: str | None = None,
        search: str | None = None,
    ) -> list[ImageGenerationList]:
        """List generation history.

        Args:
            ordering: Field to order by (e.g., "-created_at")
            search: Search query for prompt text

        Returns:
            List of generations
        """
        return await self._api.list(ordering=ordering, search=search)

    @async_api_error_handler
    async def options(self) -> ImageGenOptions:
        """Get available generation options.

        Returns:
            Available quality, style, model aliases, and default model
        """
        return await self._api.options_retrieve()

    async def wait_for_completion(
        self,
        generation_id: int | str,
        *,
        timeout: float = 300.0,
        poll_interval: float = 2.0,
    ) -> ImageGenerationDetail:
        """Wait for async generation to complete.

        Args:
            generation_id: ID of the generation to wait for
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks

        Returns:
            Completed ImageGenerationDetail

        Raises:
            TimeoutError: If generation doesn't complete within timeout
            APIError: If generation fails
        """
        start_time = time.monotonic()

        while True:
            elapsed = time.monotonic() - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"Image generation {generation_id} did not complete within {timeout}s"
                )

            status = await self.get_status(generation_id)
            logger.debug(
                "Generation %s status: %s (elapsed: %.1fs)",
                generation_id,
                status.status,
                elapsed,
            )

            if status.status == ImageGenerateResponseStatus.COMPLETED:
                return await self.get(generation_id)
            elif status.status in (
                ImageGenerateResponseStatus.FAILED,
                ImageGenerateResponseStatus.CANCELLED,
            ):
                error_msg = status.error or f"Generation {status.status}"
                raise APIError(error_msg)

            await asyncio.sleep(poll_interval)


__all__ = [
    # Resources
    "ImageGenResource",
    "AsyncImageGenResource",
    # Request/Response models
    "ImageGenerateRequestRequest",
    "ImageGenerateResponse",
    "AsyncGenerateResponse",
    "JobStatus",
    "ImageGenerationList",
    "ImageGenerationDetail",
    "ImageGenOptions",
    "ChoiceItem",
    # Enums
    "ImageGenerateRequestRequestQuality",
    "ImageGenerateRequestRequestStyle",
    "ImageGenerateResponseStatus",
]
