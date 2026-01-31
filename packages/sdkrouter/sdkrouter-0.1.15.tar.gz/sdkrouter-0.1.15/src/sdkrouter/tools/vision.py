"""Vision analysis tool using generated API client."""

from __future__ import annotations

import base64
import logging
from pathlib import Path

from .._config import SDKConfig
from ..exceptions import api_error_handler, async_api_error_handler

logger = logging.getLogger(__name__)


def _load_image_as_base64(image_path: Path | str) -> str:
    """Load image from local file and convert to base64."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")

    with open(path, "rb") as f:
        image_bytes = f.read()

    return base64.b64encode(image_bytes).decode("utf-8")
from .._api.client import (
    BaseResource,
    AsyncBaseResource,
    SyncVisionVisionAPI,
    VisionVisionAPI,
)
from .._api.generated.vision.vision__api__vision.models import (
    VisionAnalyzeRequestRequest,
    VisionAnalyzeResponse,
    OCRRequestRequest,
    OCRResponse,
    VisionModelsResponse,
)
from .._api.generated.vision.enums import (
    OCRRequestRequestMode,
    VisionAnalyzeRequestRequestModelQuality,
)


class VisionResource(BaseResource):
    """Vision analysis tool (sync).

    Uses generated SyncVisionVisionAPI client.
    """

    def __init__(self, config: SDKConfig):
        super().__init__(config)
        self._api = SyncVisionVisionAPI(self._http_client)

    @api_error_handler
    def analyze(
        self,
        *,
        image: str | None = None,
        image_url: str | None = None,
        image_path: Path | str | None = None,
        prompt: str | None = None,
        model: str | None = None,
        model_quality: VisionAnalyzeRequestRequestModelQuality | None = None,
        fetch_image: bool | None = None,
        max_tokens: int | None = None,
    ) -> VisionAnalyzeResponse:
        """
        Analyze an image with vision model.

        Args:
            image: Base64-encoded image string
            image_url: URL of the image to analyze
            image_path: Local file path (auto-converted to base64)
            prompt: Analysis prompt
            model: Specific model to use
            model_quality: Quality tier (fast/balanced/best)
            fetch_image: Whether to fetch image from URL
            max_tokens: Maximum tokens for response

        Returns:
            VisionAnalyzeResponse with description and cost

        Raises:
            ImageFetchError: If server can't fetch image from URL (use image_path instead)
            AuthenticationError: If API key is invalid
            ValidationError: If request parameters are invalid
        """
        # Auto-convert local file to base64
        if image_path is not None:
            if image is not None or image_url is not None:
                raise ValueError("Provide only one of: image, image_url, or image_path")
            logger.debug("Vision analyze: loading local file %s", image_path)
            image = _load_image_as_base64(image_path)

        logger.debug(
            "Vision analyze: image_url=%s, model=%s, quality=%s",
            image_url,
            model,
            model_quality,
        )
        # Build request with only non-None values
        kwargs = {}
        if image is not None:
            kwargs["image"] = image
        if image_url is not None:
            kwargs["image_url"] = image_url
        if prompt is not None:
            kwargs["prompt"] = prompt
        if model is not None:
            kwargs["model"] = model
        if model_quality is not None:
            kwargs["model_quality"] = model_quality
        if fetch_image is not None:
            kwargs["fetch_image"] = fetch_image
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        request = VisionAnalyzeRequestRequest(**kwargs)
        result = self._api.analyze_create(request)
        logger.info("Vision analyze completed: cost=$%.6f", result.cost_usd or 0)
        return result

    @api_error_handler
    def ocr(
        self,
        *,
        image: str | None = None,
        image_url: str | None = None,
        image_path: Path | str | None = None,
        mode: OCRRequestRequestMode | None = None,
        language_hint: str | None = None,
    ) -> OCRResponse:
        """
        Extract text from image using OCR.

        Args:
            image: Base64-encoded image string
            image_url: URL of the image
            image_path: Local file path (auto-converted to base64)
            mode: OCR mode (tiny/small/base/maximum)
            language_hint: Language hint for better accuracy

        Returns:
            OCRResponse with extracted text

        Raises:
            ImageFetchError: If server can't fetch image from URL (use image_path instead)
            AuthenticationError: If API key is invalid
        """
        # Auto-convert local file to base64
        if image_path is not None:
            if image is not None or image_url is not None:
                raise ValueError("Provide only one of: image, image_url, or image_path")
            logger.debug("Vision OCR: loading local file %s", image_path)
            image = _load_image_as_base64(image_path)

        logger.debug("Vision OCR: image_url=%s, mode=%s, language=%s", image_url, mode, language_hint)
        # Build request with only non-None values
        kwargs = {}
        if image is not None:
            kwargs["image"] = image
        if image_url is not None:
            kwargs["image_url"] = image_url
        if mode is not None:
            kwargs["mode"] = mode
        if language_hint is not None:
            kwargs["language_hint"] = language_hint
        request = OCRRequestRequest(**kwargs)
        result = self._api.ocr_create(request)
        logger.info("Vision OCR completed: %d chars extracted", len(result.text or ""))
        return result

    @api_error_handler
    def models(self) -> VisionModelsResponse:
        """Get supported vision models."""
        return self._api.models_retrieve()


class AsyncVisionResource(AsyncBaseResource):
    """Vision analysis tool (async).

    Uses generated VisionVisionAPI client.
    """

    def __init__(self, config: SDKConfig):
        super().__init__(config)
        self._api = VisionVisionAPI(self._http_client)

    @async_api_error_handler
    async def analyze(
        self,
        *,
        image: str | None = None,
        image_url: str | None = None,
        image_path: Path | str | None = None,
        prompt: str | None = None,
        model: str | None = None,
        model_quality: VisionAnalyzeRequestRequestModelQuality | None = None,
        fetch_image: bool | None = None,
        max_tokens: int | None = None,
    ) -> VisionAnalyzeResponse:
        """
        Analyze an image with vision model.

        Args:
            image: Base64-encoded image string
            image_url: URL of the image to analyze
            image_path: Local file path (auto-converted to base64)
            prompt: Analysis prompt
            model: Specific model to use
            model_quality: Quality tier (fast/balanced/best)
            fetch_image: Whether to fetch image from URL
            max_tokens: Maximum tokens for response

        Returns:
            VisionAnalyzeResponse with description and cost

        Raises:
            ImageFetchError: If server can't fetch image from URL (use image_path instead)
            AuthenticationError: If API key is invalid
            ValidationError: If request parameters are invalid
        """
        # Auto-convert local file to base64
        if image_path is not None:
            if image is not None or image_url is not None:
                raise ValueError("Provide only one of: image, image_url, or image_path")
            logger.debug("Vision async analyze: loading local file %s", image_path)
            image = _load_image_as_base64(image_path)

        logger.debug(
            "Vision async analyze: image_url=%s, model=%s, quality=%s",
            image_url,
            model,
            model_quality,
        )
        # Build request with only non-None values
        kwargs = {}
        if image is not None:
            kwargs["image"] = image
        if image_url is not None:
            kwargs["image_url"] = image_url
        if prompt is not None:
            kwargs["prompt"] = prompt
        if model is not None:
            kwargs["model"] = model
        if model_quality is not None:
            kwargs["model_quality"] = model_quality
        if fetch_image is not None:
            kwargs["fetch_image"] = fetch_image
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        request = VisionAnalyzeRequestRequest(**kwargs)
        result = await self._api.analyze_create(request)
        logger.info("Vision analyze completed: cost=$%.6f", result.cost_usd or 0)
        return result

    @async_api_error_handler
    async def ocr(
        self,
        *,
        image: str | None = None,
        image_url: str | None = None,
        image_path: Path | str | None = None,
        mode: OCRRequestRequestMode | None = None,
        language_hint: str | None = None,
    ) -> OCRResponse:
        """
        Extract text from image using OCR.

        Args:
            image: Base64-encoded image string
            image_url: URL of the image
            image_path: Local file path (auto-converted to base64)
            mode: OCR mode (tiny/small/base/maximum)
            language_hint: Language hint for better accuracy

        Returns:
            OCRResponse with extracted text

        Raises:
            ImageFetchError: If server can't fetch image from URL (use image_path instead)
            AuthenticationError: If API key is invalid
        """
        # Auto-convert local file to base64
        if image_path is not None:
            if image is not None or image_url is not None:
                raise ValueError("Provide only one of: image, image_url, or image_path")
            logger.debug("Vision async OCR: loading local file %s", image_path)
            image = _load_image_as_base64(image_path)

        logger.debug("Vision async OCR: image_url=%s, mode=%s, language=%s", image_url, mode, language_hint)
        # Build request with only non-None values
        kwargs = {}
        if image is not None:
            kwargs["image"] = image
        if image_url is not None:
            kwargs["image_url"] = image_url
        if mode is not None:
            kwargs["mode"] = mode
        if language_hint is not None:
            kwargs["language_hint"] = language_hint
        request = OCRRequestRequest(**kwargs)
        result = await self._api.ocr_create(request)
        logger.info("Vision OCR completed: %d chars extracted", len(result.text or ""))
        return result

    @async_api_error_handler
    async def models(self) -> VisionModelsResponse:
        """Get supported vision models."""
        return await self._api.models_retrieve()


__all__ = [
    "VisionResource",
    "AsyncVisionResource",
    # Models
    "VisionAnalyzeRequestRequest",
    "VisionAnalyzeResponse",
    "OCRRequestRequest",
    "OCRResponse",
    "VisionModelsResponse",
    # Enums
    "OCRRequestRequestMode",
    "VisionAnalyzeRequestRequestModelQuality",
]
