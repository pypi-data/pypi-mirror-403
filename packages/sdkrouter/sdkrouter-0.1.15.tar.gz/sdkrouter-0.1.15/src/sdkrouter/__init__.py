"""
SDKRouter - Unified SDK for AI services with OpenAI compatibility.

Example:
    ```python
    from sdkrouter import SDKRouter

    # Initialize client
    client = SDKRouter(api_key="your-api-key")

    # OpenAI-compatible chat
    response = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[{"role": "user", "content": "Hello!"}],
    )
    print(response.choices[0].message.content)

    # Vision analysis
    result = client.vision.analyze(image_url="https://example.com/image.jpg")
    print(result.description)

    # CDN upload
    from pathlib import Path
    file = client.cdn.upload(Path("image.png"), ttl="7d")
    print(file.url)
    ```
"""

from ._version import __version__
from ._client import SDKRouter, AsyncSDKRouter
from ._config import SDKConfig, get_config, configure, reset_config

# Logging
from .logging import (
    get_logger,
    setup_logging,
    find_project_root,
    get_log_dir,
    reset_logging,
    LogLevel,
    RICH_AVAILABLE,
)

# API Client utilities
from ._api import HTTPClientFactory, BaseResource, AsyncBaseResource

# Types
from ._types.vision import VisionAnalyzeRequest, VisionAnalyzeResponse
from ._types.ocr import OCRRequest, OCRResponse
from ._types.cdn import CDNFile, CDNUploadRequest
from ._types.shortlinks import ShortLink, ShortLinkCreateRequest
from ._types.models import ModelInfo, ModelPricing
from .models import Model, Tier, Category, Capability
from ._types.parsed import ParsedChatCompletion, ParsedChoice, ParsedMessage

# Search types
from .tools.search import SearchResponse, Citation, UserLocation, SearchMode

# Embedding types
from .tools.embeddings import EmbeddingResponse, EmbeddingData, EmbeddingUsage

# Audio types
from ._types.audio import (
    TranscriptionResponse,
    TranscriptionSegment,
    VerboseTranscriptionResponse,
    TranscriptionResponseFormat,
    SpeechRequest,
    TTSVoice,
    TTSResponseFormat,
    AudioAnalysisFrame,
    AudioAnalysis,
    SpeechResponse,
    SpeechStreamChunk,
    SpeechStreamDone,
    AudioModelInfo,
    AudioModelsResponse,
)
from .models import AudioModel
from .tools.audio import AudioResource, AsyncAudioResource

# Image Gen types
from .tools.image_gen import (
    ImageGenResource,
    AsyncImageGenResource,
    ImageGenerateResponse,
    ImageGenerationDetail,
    ImageGenOptions,
    ImageGenerateRequestRequestQuality,
    ImageGenerateRequestRequestStyle,
    ImageGenerateResponseStatus,
)

# Payments types
from .tools.payments import (
    PaymentsResource,
    AsyncPaymentsResource,
    Balance,
    Currency,
    CurrencyEstimateResponse,
    PaymentDetail,
    PaymentStatus,
    PaymentCreateResponse,
    Transaction,
    WithdrawalDetail,
    WithdrawalCreateResponse,
)

# Helpers (from archive)
from .helpers import json_to_toon, JsonCleaner, html_to_text, extract_links, extract_images

# Exceptions
from .exceptions import (
    SDKRouterError,
    APIError,
    ImageFetchError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    TimeoutError,
    NetworkError,
    NotFoundError,
)

# Utilities
from .utils import (
    TokenCounter,
    count_tokens,
    count_messages_tokens,
    estimate_image_tokens,
    get_optimal_detail_mode,
    # Parsing utilities
    ResponseFormatT,
    to_strict_json_schema,
    type_to_response_format,
)

__all__ = [
    # Version
    "__version__",
    # Clients
    "SDKRouter",
    "AsyncSDKRouter",
    # Configuration
    "SDKConfig",
    "get_config",
    "configure",
    "reset_config",
    # Logging
    "get_logger",
    "setup_logging",
    "find_project_root",
    "get_log_dir",
    "reset_logging",
    "LogLevel",
    "RICH_AVAILABLE",
    # API utilities
    "HTTPClientFactory",
    "BaseResource",
    "AsyncBaseResource",
    # Vision types
    "VisionAnalyzeRequest",
    "VisionAnalyzeResponse",
    # OCR types
    "OCRRequest",
    "OCRResponse",
    # CDN types
    "CDNFile",
    "CDNUploadRequest",
    # Shortlinks types
    "ShortLink",
    "ShortLinkCreateRequest",
    # Model alias builder
    "Model",
    # Model enums
    "Tier",
    "Category",
    "Capability",
    # Model types
    "ModelInfo",
    "ModelPricing",
    # Parsed types (structured output)
    "ParsedChatCompletion",
    "ParsedChoice",
    "ParsedMessage",
    # Helpers
    "json_to_toon",
    "JsonCleaner",
    "html_to_text",
    "extract_links",
    "extract_images",
    # Token utilities
    "TokenCounter",
    "count_tokens",
    "count_messages_tokens",
    "estimate_image_tokens",
    "get_optimal_detail_mode",
    # Parsing utilities
    "ResponseFormatT",
    "to_strict_json_schema",
    "type_to_response_format",
    # Search types
    "SearchResponse",
    "Citation",
    "UserLocation",
    "SearchMode",
    # Embedding types
    "EmbeddingResponse",
    "EmbeddingData",
    "EmbeddingUsage",
    # Image Gen types
    "ImageGenResource",
    "AsyncImageGenResource",
    "ImageGenerateResponse",
    "ImageGenerationDetail",
    "ImageGenOptions",
    "ImageGenerateRequestRequestQuality",
    "ImageGenerateRequestRequestStyle",
    "ImageGenerateResponseStatus",
    # Audio model builder
    "AudioModel",
    # Audio types
    "TranscriptionResponse",
    "TranscriptionSegment",
    "VerboseTranscriptionResponse",
    "TranscriptionResponseFormat",
    "SpeechRequest",
    "TTSVoice",
    "TTSResponseFormat",
    "SpeechStreamChunk",
    "SpeechStreamDone",
    "AudioModelInfo",
    "AudioModelsResponse",
    # Audio resources
    "AudioResource",
    "AsyncAudioResource",
    # Payments resources
    "PaymentsResource",
    "AsyncPaymentsResource",
    # Payments types
    "Balance",
    "Currency",
    "CurrencyEstimateResponse",
    "PaymentDetail",
    "PaymentStatus",
    "PaymentCreateResponse",
    "Transaction",
    "WithdrawalDetail",
    "WithdrawalCreateResponse",
    # Exceptions
    "SDKRouterError",
    "APIError",
    "ImageFetchError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "TimeoutError",
    "NetworkError",
    "NotFoundError",
]
