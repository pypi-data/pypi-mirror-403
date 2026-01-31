from __future__ import annotations

import httpx

from .models import (
    OCRRequestRequest,
    OCRResponse,
    VisionAnalyzeRequestRequest,
    VisionAnalyzeResponse,
    VisionModelsResponse,
)


class SyncVisionVisionAPI:
    """Synchronous API endpoints for Vision."""

    def __init__(self, client: httpx.Client):
        """Initialize sync sub-client with shared httpx client."""
        self._client = client

    def analyze_create(self, data: VisionAnalyzeRequestRequest) -> VisionAnalyzeResponse:
        """
        Analyze image

        Analyze an image with vision model.
        """
        url = "/api/vision/analyze/"
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
        return VisionAnalyzeResponse.model_validate(response.json())


    def models_retrieve(self) -> VisionModelsResponse:
        """
        Get vision models

        Get supported vision models.
        """
        url = "/api/vision/models/"
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
        return VisionModelsResponse.model_validate(response.json())


    def ocr_create(self, data: OCRRequestRequest) -> OCRResponse:
        """
        OCR extraction

        Extract text from image using OCR.
        """
        url = "/api/vision/ocr/"
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
        return OCRResponse.model_validate(response.json())


