"""Type definitions for SDK resources."""

from .cdn import CDNFile, CDNUploadRequest
from .models import ModelInfo, ModelPricing
from .ocr import OCRRequest, OCRResponse
from .parsed import ParsedChatCompletion, ParsedChoice, ParsedMessage
from .shortlinks import ShortLink, ShortLinkCreateRequest
from .vision import VisionAnalyzeRequest, VisionAnalyzeResponse

__all__ = [
    # CDN
    "CDNFile",
    "CDNUploadRequest",
    # Models
    "ModelInfo",
    "ModelPricing",
    # OCR
    "OCRRequest",
    "OCRResponse",
    # Parsed (structured output)
    "ParsedChatCompletion",
    "ParsedChoice",
    "ParsedMessage",
    # Shortlinks
    "ShortLink",
    "ShortLinkCreateRequest",
    # Vision
    "VisionAnalyzeRequest",
    "VisionAnalyzeResponse",
]
