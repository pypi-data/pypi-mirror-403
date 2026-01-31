from __future__ import annotations

import httpx

from .models import (
    AsyncGenerateResponse,
    ImageGenOptions,
    ImageGenerateRequestRequest,
    ImageGenerateResponse,
    ImageGenerationDetail,
    ImageGenerationList,
    JobStatus,
)


class SyncImageGenImageGenAPI:
    """Synchronous API endpoints for Image Gen."""

    def __init__(self, client: httpx.Client):
        """Initialize sync sub-client with shared httpx client."""
        self._client = client

    def list(
        self,
        ordering: str | None = None,
        search: str | None = None,
    ) -> list[ImageGenerationList]:
        """
        List generation history

        List image generation history for the current API key.
        """
        url = "/api/image_gen/"
        response = self._client.get(url, params={"ordering": ordering if ordering is not None else None, "search": search if search is not None else None})
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return [ImageGenerationList.model_validate(item) for item in response.json()]


    def retrieve(self, id: str) -> ImageGenerationDetail:
        """
        Get generation details

        Get detailed information about a specific generation.
        """
        url = f"/api/image_gen/{id}/"
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
        return ImageGenerationDetail.model_validate(response.json())


    def status_retrieve(self, id: str) -> JobStatus:
        """
        Get job status

        Get status of async generation job.
        """
        url = f"/api/image_gen/{id}/status/"
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
        return JobStatus.model_validate(response.json())


    def generate_create(self, data: ImageGenerateRequestRequest) -> ImageGenerateResponse:
        """
        Generate images (sync)

        Generate images synchronously. Use model aliases like @cheap, @balanced,
        @smart for automatic model selection, or specify explicit model ID.
        """
        url = "/api/image_gen/generate/"
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
        return ImageGenerateResponse.model_validate(response.json())


    def generate_async_create(
        self,
        data: ImageGenerateRequestRequest,
    ) -> AsyncGenerateResponse:
        """
        Generate images (async)

        Start async image generation using RQ. Returns job ID for status
        tracking. Use GET /api/image_gen/{id}/status/ to check progress.
        """
        url = "/api/image_gen/generate-async/"
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
        return AsyncGenerateResponse.model_validate(response.json())


    def options_retrieve(self) -> ImageGenOptions:
        """
        Get available options

        Get available options for image generation: quality, style, model
        aliases.
        """
        url = "/api/image_gen/options/"
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
        return ImageGenOptions.model_validate(response.json())


