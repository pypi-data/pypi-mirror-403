"""Main SDK client classes."""

import json
import logging
import os
from typing import Any, Optional, Type, cast

from openai import AsyncOpenAI, OpenAI

from ._config import SDKConfig

logger = logging.getLogger(__name__)
from ._constants import (
    DEFAULT_API_URL,
    DEFAULT_AUDIO_URL,
    DEFAULT_LLM_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    ENV_API_KEY,
    ENV_AUDIO_URL,
    ENV_OPENROUTER_KEY,
    OPENROUTER_URL,
)
from ._types.parsed import ParsedChatCompletion, ParsedChoice
from .tools.vision import AsyncVisionResource, VisionResource
from .tools.cdn import AsyncCDNResource, CDNResource
from .tools.shortlinks import AsyncShortlinksResource, ShortlinksResource
from .tools.keys import AsyncKeysResource, KeysResource
from .tools.cleaner import AsyncCleanerResource, CleanerResource
from .tools.models import AsyncModelsResource, ModelsResource
from .tools.search import AsyncSearchResource, SearchResource
from .tools.embeddings import AsyncEmbeddingsResource, EmbeddingsResource
from .tools.image_gen import AsyncImageGenResource, ImageGenResource
from .tools.audio import AsyncAudioResource, AudioResource
from .tools.payments import AsyncPaymentsResource, PaymentsResource
from .tools.proxies import AsyncProxiesResource, ProxiesResource
from .utils.parsing import ResponseFormatT, type_to_response_format


def _parse_completion(
    raw_response: Any,
    response_format: Type[ResponseFormatT],
) -> ParsedChatCompletion[ResponseFormatT]:
    """
    Parse raw ChatCompletion into ParsedChatCompletion with typed content.

    Args:
        raw_response: Raw ChatCompletion from OpenAI API
        response_format: Pydantic model class for parsing

    Returns:
        ParsedChatCompletion with parsed content in each choice
    """
    parsed_choices: list[ParsedChoice[ResponseFormatT]] = []

    for choice in raw_response.choices:
        parsed_content = None
        content = getattr(choice.message, "content", None)

        if content:
            try:
                data = json.loads(content)
                parsed_content = response_format.model_validate(data)
            except json.JSONDecodeError as e:
                logger.warning(
                    "Failed to parse JSON response: %s (content: %.100s...)",
                    e,
                    content,
                )
            except Exception as e:
                logger.warning(
                    "Failed to validate response with %s: %s",
                    response_format.__name__,
                    e,
                )

        parsed_choices.append(
            ParsedChoice.from_choice(choice, parsed_content=parsed_content)
        )

    return ParsedChatCompletion.from_completion(raw_response, parsed_choices)


class SDKRouter(OpenAI):
    """
    Main SDK client - OpenAI-compatible with additional tools.

    Extends OpenAI client with vision, OCR, CDN, and shortlinks tools.

    Example:
        ```python
        from sdkrouter import SDKRouter

        client = SDKRouter(api_key="your-api-key")

        # OpenAI-compatible chat
        response = client.chat.completions.create(
            model="openai/gpt-4o",
            messages=[{"role": "user", "content": "Hello!"}],
        )

        # Vision analysis
        result = client.vision.analyze(image_url="https://example.com/image.jpg")

        # CDN upload
        file = client.cdn.upload(Path("image.png"))
        ```
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        llm_url: Optional[str] = None,
        api_url: Optional[str] = None,
        audio_url: Optional[str] = None,
        use_self_hosted: bool = True,
        openrouter_api_key: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        **kwargs,
    ):
        """
        Initialize SDKRouter client.

        Args:
            api_key: API key (or set SDKROUTER_API_KEY env var)
            llm_url: FastAPI URL for LLM endpoints (chat, embeddings) - OpenAI-compatible
                    Default: https://llm.sdkrouter.com
            api_url: Django URL for REST API endpoints (CDN, vision, shortlinks)
                    Default: https://api.sdkrouter.com
            audio_url: FastAPI URL for Audio endpoints (STT, TTS) - OpenAI-compatible
                    Default: https://audio.sdkrouter.com
            use_self_hosted: If True, use self-hosted proxy. If False, direct to OpenRouter
            openrouter_api_key: OpenRouter API key (for direct mode)
            timeout: Request timeout in seconds
            max_retries: Number of retries for failed requests
            **kwargs: Additional arguments passed to OpenAI client
        """
        # Resolve API key
        resolved_key = (
            api_key
            or os.getenv(ENV_API_KEY)
            or openrouter_api_key
            or os.getenv(ENV_OPENROUTER_KEY)
        )
        if not resolved_key:
            logger.error("API key not provided and not found in environment")
            raise ValueError(
                "API key required. Set SDKROUTER_API_KEY environment variable "
                "or pass api_key= parameter."
            )

        # Resolve URLs
        resolved_audio_url = audio_url or os.getenv(ENV_AUDIO_URL) or DEFAULT_AUDIO_URL
        if use_self_hosted:
            resolved_llm_url = llm_url or os.getenv("SDKROUTER_LLM_URL") or DEFAULT_LLM_URL
            resolved_api_url = api_url or os.getenv("SDKROUTER_API_URL") or DEFAULT_API_URL
        else:
            resolved_llm_url = OPENROUTER_URL
            resolved_api_url = api_url or DEFAULT_API_URL

        # Log initialization
        logger.debug(
            "SDKRouter initializing: llm_url=%s, api_url=%s, audio_url=%s, self_hosted=%s, timeout=%s",
            resolved_llm_url,
            resolved_api_url,
            resolved_audio_url,
            use_self_hosted,
            timeout,
        )

        # Remove base_url from kwargs if present (we handle it ourselves)
        kwargs.pop("base_url", None)

        # Initialize OpenAI client (uses llm_url for chat/completions)
        super().__init__(
            api_key=resolved_key,
            base_url=resolved_llm_url,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs,
        )

        logger.info("SDKRouter initialized successfully")

        # Store configuration
        self._sdk_config = SDKConfig(
            api_key=resolved_key,
            llm_url=resolved_llm_url,
            api_url=resolved_api_url,
            audio_url=resolved_audio_url,
            use_self_hosted=use_self_hosted,
            timeout=timeout,
            max_retries=max_retries,
        )

        # Lazy-loaded tool resources
        self._vision: Optional[VisionResource] = None
        self._cdn: Optional[CDNResource] = None
        self._shortlinks: Optional[ShortlinksResource] = None
        self._keys: Optional[KeysResource] = None
        self._api_cleaner: Optional[CleanerResource] = None
        self._models: Optional[ModelsResource] = None
        self._search: Optional[SearchResource] = None
        self._embeddings: Optional[EmbeddingsResource] = None
        self._image_gen: Optional[ImageGenResource] = None
        self._audio: Optional[AudioResource] = None
        self._payments: Optional[PaymentsResource] = None
        self._proxies: Optional[ProxiesResource] = None

    @property
    def vision(self) -> VisionResource:
        """Vision analysis and OCR tool."""
        if self._vision is None:
            self._vision = VisionResource(self._sdk_config)
        return self._vision

    @property
    def cdn(self) -> CDNResource:
        """CDN file storage tool."""
        if self._cdn is None:
            self._cdn = CDNResource(self._sdk_config)
        return self._cdn

    @property
    def shortlinks(self) -> ShortlinksResource:
        """URL shortening tool."""
        if self._shortlinks is None:
            self._shortlinks = ShortlinksResource(self._sdk_config)
        return self._shortlinks

    @property
    def keys(self) -> KeysResource:
        """API keys management tool."""
        if self._keys is None:
            self._keys = KeysResource(self._sdk_config)
        return self._keys

    @property
    def api_cleaner(self) -> CleanerResource:
        """HTML cleaner tool (API-based, server-side)."""
        if self._api_cleaner is None:
            self._api_cleaner = CleanerResource(self._sdk_config)
        return self._api_cleaner

    @property
    def llm_models(self) -> ModelsResource:
        """LLM models listing tool."""
        if self._models is None:
            self._models = ModelsResource(self._sdk_config)
        return self._models

    @property
    def search(self) -> SearchResource:
        """Web search tool."""
        if self._search is None:
            self._search = SearchResource(self._sdk_config)
        return self._search

    @property
    def embeddings(self) -> EmbeddingsResource:  # type: ignore[override]
        """Embeddings tool."""
        if self._embeddings is None:
            self._embeddings = EmbeddingsResource(self._sdk_config)
        return self._embeddings

    @property
    def image_gen(self) -> ImageGenResource:
        """Image generation tool."""
        if self._image_gen is None:
            self._image_gen = ImageGenResource(self._sdk_config)
        return self._image_gen

    @property
    def audio(self) -> AudioResource:  # type: ignore[override]
        """Audio transcription (STT) and speech (TTS) tool."""
        if self._audio is None:
            self._audio = AudioResource(self._sdk_config)
        return self._audio

    @property
    def payments(self) -> PaymentsResource:
        """Cryptocurrency payments tool."""
        if self._payments is None:
            self._payments = PaymentsResource(self._sdk_config)
        return self._payments

    @property
    def proxies(self) -> ProxiesResource:
        """Proxy management tool."""
        if self._proxies is None:
            self._proxies = ProxiesResource(self._sdk_config)
        return self._proxies

    @property
    def config(self) -> SDKConfig:
        """SDK configuration."""
        return self._sdk_config

    def parse(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        response_format: Type[ResponseFormatT],
        **kwargs: Any,
    ) -> ParsedChatCompletion[ResponseFormatT]:
        """
        Create chat completion with structured output.

        Automatically converts Pydantic model to JSON Schema and parses
        the response back into the model.

        Args:
            model: Model ID (e.g., "openai/gpt-4o")
            messages: Chat messages
            response_format: Pydantic model class for response parsing
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            ParsedChatCompletion with .choices[0].message.parsed

        Example:
            ```python
            class MathResponse(BaseModel):
                steps: list[str]
                answer: float

            result = client.parse(
                model="openai/gpt-4o",
                messages=[{"role": "user", "content": "Solve 2+2"}],
                response_format=MathResponse,
            )
            print(result.choices[0].message.parsed.answer)
            ```
        """
        # Convert Pydantic model to response_format
        format_param = type_to_response_format(response_format)

        # Make API call
        raw_response = self.chat.completions.create(
            model=model,
            messages=cast(Any, messages),
            response_format=cast(Any, format_param),
            **kwargs,
        )

        # Parse response
        return _parse_completion(raw_response, response_format)


class AsyncSDKRouter(AsyncOpenAI):
    """
    Async SDK client - OpenAI-compatible with additional tools.

    Async version of SDKRouter for use in async contexts.

    Example:
        ```python
        from sdkrouter import AsyncSDKRouter

        client = AsyncSDKRouter(api_key="your-api-key")

        # Async chat
        response = await client.chat.completions.create(
            model="openai/gpt-4o",
            messages=[{"role": "user", "content": "Hello!"}],
        )

        # Async vision
        result = await client.vision.analyze(image_url="https://example.com/image.jpg")
        ```
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        llm_url: Optional[str] = None,
        api_url: Optional[str] = None,
        audio_url: Optional[str] = None,
        use_self_hosted: bool = True,
        openrouter_api_key: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        **kwargs,
    ):
        """Initialize async SDKRouter client."""
        # Resolve API key
        resolved_key = (
            api_key
            or os.getenv(ENV_API_KEY)
            or openrouter_api_key
            or os.getenv(ENV_OPENROUTER_KEY)
        )
        if not resolved_key:
            logger.error("API key not provided and not found in environment")
            raise ValueError(
                "API key required. Set SDKROUTER_API_KEY environment variable "
                "or pass api_key= parameter."
            )

        # Resolve URLs
        resolved_audio_url = audio_url or os.getenv(ENV_AUDIO_URL) or DEFAULT_AUDIO_URL
        if use_self_hosted:
            resolved_llm_url = llm_url or os.getenv("SDKROUTER_LLM_URL") or DEFAULT_LLM_URL
            resolved_api_url = api_url or os.getenv("SDKROUTER_API_URL") or DEFAULT_API_URL
        else:
            resolved_llm_url = OPENROUTER_URL
            resolved_api_url = api_url or DEFAULT_API_URL

        # Log initialization
        logger.debug(
            "AsyncSDKRouter initializing: llm_url=%s, api_url=%s, audio_url=%s, self_hosted=%s, timeout=%s",
            resolved_llm_url,
            resolved_api_url,
            resolved_audio_url,
            use_self_hosted,
            timeout,
        )

        # Remove base_url from kwargs if present (we handle it ourselves)
        kwargs.pop("base_url", None)

        # Initialize AsyncOpenAI client (uses llm_url for chat/completions)
        super().__init__(
            api_key=resolved_key,
            base_url=resolved_llm_url,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs,
        )

        logger.info("AsyncSDKRouter initialized successfully")

        # Store configuration
        self._sdk_config = SDKConfig(
            api_key=resolved_key,
            llm_url=resolved_llm_url,
            api_url=resolved_api_url,
            audio_url=resolved_audio_url,
            use_self_hosted=use_self_hosted,
            timeout=timeout,
            max_retries=max_retries,
        )

        # Lazy-loaded async tool resources
        self._vision: Optional[AsyncVisionResource] = None
        self._cdn: Optional[AsyncCDNResource] = None
        self._shortlinks: Optional[AsyncShortlinksResource] = None
        self._keys: Optional[AsyncKeysResource] = None
        self._api_cleaner: Optional[AsyncCleanerResource] = None
        self._models: Optional[AsyncModelsResource] = None
        self._search: Optional[AsyncSearchResource] = None
        self._embeddings: Optional[AsyncEmbeddingsResource] = None
        self._image_gen: Optional[AsyncImageGenResource] = None
        self._audio: Optional[AsyncAudioResource] = None
        self._payments: Optional[AsyncPaymentsResource] = None
        self._proxies: Optional[AsyncProxiesResource] = None

    @property
    def vision(self) -> AsyncVisionResource:
        """Vision analysis and OCR tool (async)."""
        if self._vision is None:
            self._vision = AsyncVisionResource(self._sdk_config)
        return self._vision

    @property
    def cdn(self) -> AsyncCDNResource:
        """CDN file storage tool (async)."""
        if self._cdn is None:
            self._cdn = AsyncCDNResource(self._sdk_config)
        return self._cdn

    @property
    def shortlinks(self) -> AsyncShortlinksResource:
        """URL shortening tool (async)."""
        if self._shortlinks is None:
            self._shortlinks = AsyncShortlinksResource(self._sdk_config)
        return self._shortlinks

    @property
    def keys(self) -> AsyncKeysResource:
        """API keys management tool (async)."""
        if self._keys is None:
            self._keys = AsyncKeysResource(self._sdk_config)
        return self._keys

    @property
    def api_cleaner(self) -> AsyncCleanerResource:
        """HTML cleaner tool (async, API-based, server-side)."""
        if self._api_cleaner is None:
            self._api_cleaner = AsyncCleanerResource(self._sdk_config)
        return self._api_cleaner

    @property
    def llm_models(self) -> AsyncModelsResource:
        """LLM models listing tool (async)."""
        if self._models is None:
            self._models = AsyncModelsResource(self._sdk_config)
        return self._models

    @property
    def search(self) -> AsyncSearchResource:
        """Web search tool (async)."""
        if self._search is None:
            self._search = AsyncSearchResource(self._sdk_config)
        return self._search

    @property
    def embeddings(self) -> AsyncEmbeddingsResource:  # type: ignore[override]
        """Embeddings tool (async)."""
        if self._embeddings is None:
            self._embeddings = AsyncEmbeddingsResource(self._sdk_config)
        return self._embeddings

    @property
    def image_gen(self) -> AsyncImageGenResource:
        """Image generation tool (async)."""
        if self._image_gen is None:
            self._image_gen = AsyncImageGenResource(self._sdk_config)
        return self._image_gen

    @property
    def audio(self) -> AsyncAudioResource:  # type: ignore[override]
        """Audio transcription (STT) and speech (TTS) tool (async)."""
        if self._audio is None:
            self._audio = AsyncAudioResource(self._sdk_config)
        return self._audio

    @property
    def payments(self) -> AsyncPaymentsResource:
        """Cryptocurrency payments tool (async)."""
        if self._payments is None:
            self._payments = AsyncPaymentsResource(self._sdk_config)
        return self._payments

    @property
    def proxies(self) -> AsyncProxiesResource:
        """Proxy management tool (async)."""
        if self._proxies is None:
            self._proxies = AsyncProxiesResource(self._sdk_config)
        return self._proxies

    @property
    def config(self) -> SDKConfig:
        """SDK configuration."""
        return self._sdk_config

    async def parse(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        response_format: Type[ResponseFormatT],
        **kwargs: Any,
    ) -> ParsedChatCompletion[ResponseFormatT]:
        """
        Create async chat completion with structured output.

        Automatically converts Pydantic model to JSON Schema and parses
        the response back into the model.

        Args:
            model: Model ID (e.g., "openai/gpt-4o")
            messages: Chat messages
            response_format: Pydantic model class for response parsing
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            ParsedChatCompletion with .choices[0].message.parsed

        Example:
            ```python
            class MathResponse(BaseModel):
                steps: list[str]
                answer: float

            result = await client.parse(
                model="openai/gpt-4o",
                messages=[{"role": "user", "content": "Solve 2+2"}],
                response_format=MathResponse,
            )
            print(result.choices[0].message.parsed.answer)
            ```
        """
        # Convert Pydantic model to response_format
        format_param = type_to_response_format(response_format)

        # Make API call
        raw_response = await self.chat.completions.create(
            model=model,
            messages=cast(Any, messages),
            response_format=cast(Any, format_param),
            **kwargs,
        )

        # Parse response
        return _parse_completion(raw_response, response_format)
