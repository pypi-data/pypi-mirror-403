"""
SDKRouter API Client Utilities.

Provides:
- HTTPClientFactory: Creates configured httpx clients
- BaseResource: Base class for sync tool resources
- AsyncBaseResource: Base class for async tool resources
- Generated API clients (sync and async) for all tools

All tools inherit from base classes to ensure consistent
HTTP client configuration and authentication.

Example:
    >>> from sdkrouter._api.client import BaseResource, SyncVisionVisionAPI
    >>>
    >>> class VisionResource(BaseResource):
    ...     def __init__(self, config):
    ...         super().__init__(config)
    ...         self._api = SyncVisionVisionAPI(self._http_client)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .._config import SDKConfig

# ============================================================================
# Generated API Clients (Async)
# ============================================================================
from .generated.vision.vision__api__vision import VisionVisionAPI
from .generated.cdn.cdn__api__cdn import CdnCdnAPI
from .generated.sdk_keys.sdk_keys__api__sdk_keys import SdkKeysSdkKeysAPI
from .generated.shortlinks.shortlinks__api__shortlinks import ShortlinksShortlinksAPI
from .generated.cleaner.cleaner__api__cleaner import CleanerCleanerAPI
from .generated.models.models__api__llm_models import ModelsLlmModelsAPI
from .generated.search.search__api__search import SearchSearchAPI
from .generated.image_gen.image_gen__api__image_gen import ImageGenImageGenAPI
from .generated.payments.payments__api__payments import PaymentsPaymentsAPI
from .generated.proxies.proxies__api__proxies import ProxiesProxiesAPI

# ============================================================================
# Generated API Clients (Sync)
# ============================================================================
from .generated.vision.vision__api__vision.sync_client import SyncVisionVisionAPI
from .generated.cdn.cdn__api__cdn.sync_client import SyncCdnCdnAPI
from .generated.sdk_keys.sdk_keys__api__sdk_keys.sync_client import SyncSdkKeysSdkKeysAPI
from .generated.shortlinks.shortlinks__api__shortlinks.sync_client import SyncShortlinksShortlinksAPI
from .generated.cleaner.cleaner__api__cleaner.sync_client import SyncCleanerCleanerAPI
from .generated.models.models__api__llm_models.sync_client import SyncModelsLlmModelsAPI
from .generated.search.search__api__search.sync_client import SyncSearchSearchAPI
from .generated.image_gen.image_gen__api__image_gen.sync_client import SyncImageGenImageGenAPI
from .generated.payments.payments__api__payments.sync_client import SyncPaymentsPaymentsAPI
from .generated.proxies.proxies__api__proxies.sync_client import SyncProxiesProxiesAPI


class HTTPClientFactory:
    """
    Factory for creating configured httpx clients.

    Creates sync/async HTTP clients with:
    - Base URL from config (api_url for Django, llm_url for FastAPI)
    - Bearer token authentication
    - Configured timeout

    Example:
        >>> factory = HTTPClientFactory(sdk_config)
        >>> # Django API client (CDN, vision, shortlinks, etc.)
        >>> api_client = factory.create_sync_client()
        >>> # FastAPI client (chat, embeddings)
        >>> openai_client = factory.create_sync_client(use_llm_url=True)
    """

    def __init__(self, config: "SDKConfig"):
        """
        Initialize factory with SDK configuration.

        Args:
            config: SDKConfig with api_url, llm_url, api_key, timeout
        """
        self._config = config

    def _get_headers(self) -> dict[str, str]:
        """Build request headers with auth token."""
        return {"Authorization": f"Bearer {self._config.api_key}"}

    def _resolve_base_url(
        self, *, use_llm_url: bool = False, use_audio_url: bool = False
    ) -> str:
        """Resolve base URL from flags."""
        if use_audio_url:
            return self._config.audio_url
        if use_llm_url:
            return self._config.llm_url
        return self._config.api_url

    def create_sync_client(
        self, *, use_llm_url: bool = False, use_audio_url: bool = False
    ) -> httpx.Client:
        """
        Create a synchronous HTTP client.

        Args:
            use_llm_url: If True, use llm_url (FastAPI LLM). Default uses api_url (Django).
            use_audio_url: If True, use audio_url (FastAPI Audio).

        Returns:
            Configured httpx.Client with base_url, auth headers, timeout
        """
        base_url = self._resolve_base_url(use_llm_url=use_llm_url, use_audio_url=use_audio_url)
        logger.debug(
            "Creating sync HTTP client: base_url=%s, timeout=%s",
            base_url,
            self._config.timeout,
        )
        return httpx.Client(
            base_url=base_url,
            headers=self._get_headers(),
            timeout=self._config.timeout,
        )

    def create_async_client(
        self, *, use_llm_url: bool = False, use_audio_url: bool = False
    ) -> httpx.AsyncClient:
        """
        Create an asynchronous HTTP client.

        Args:
            use_llm_url: If True, use llm_url (FastAPI LLM). Default uses api_url (Django).
            use_audio_url: If True, use audio_url (FastAPI Audio).

        Returns:
            Configured httpx.AsyncClient with base_url, auth headers, timeout
        """
        base_url = self._resolve_base_url(use_llm_url=use_llm_url, use_audio_url=use_audio_url)
        logger.debug(
            "Creating async HTTP client: base_url=%s, timeout=%s",
            base_url,
            self._config.timeout,
        )
        return httpx.AsyncClient(
            base_url=base_url,
            headers=self._get_headers(),
            timeout=self._config.timeout,
        )


class BaseResource:
    """
    Base class for synchronous tool resources.

    Provides:
    - HTTP client creation via HTTPClientFactory
    - Access to SDK config
    - Common http_client property

    Subclasses should initialize their generated API client in __init__:

        class VisionResource(BaseResource):
            def __init__(self, config: SDKConfig):
                super().__init__(config)
                self._api = SyncVisionVisionAPI(self._http_client)

        # For OpenAI-compatible endpoints (embeddings):
        class EmbeddingsResource(BaseResource):
            def __init__(self, config: SDKConfig):
                super().__init__(config, use_llm_url=True)
    """

    def __init__(
        self, config: "SDKConfig", *, use_llm_url: bool = False, use_audio_url: bool = False
    ):
        """
        Initialize resource with SDK configuration.

        Args:
            config: SDKConfig with api_url, llm_url, audio_url, api_key, timeout
            use_llm_url: If True, use llm_url (FastAPI LLM). Default uses api_url (Django).
            use_audio_url: If True, use audio_url (FastAPI Audio).
        """
        self._config = config
        self._factory = HTTPClientFactory(config)
        self._http_client = self._factory.create_sync_client(
            use_llm_url=use_llm_url, use_audio_url=use_audio_url,
        )

    @property
    def http_client(self) -> httpx.Client:
        """Access the underlying HTTP client for direct requests."""
        return self._http_client

    @property
    def config(self) -> "SDKConfig":
        """Access the SDK configuration."""
        return self._config


class AsyncBaseResource:
    """
    Base class for asynchronous tool resources.

    Provides:
    - HTTP client creation via HTTPClientFactory
    - Access to SDK config
    - Common http_client property

    Subclasses should initialize their generated API client in __init__:

        class AsyncVisionResource(AsyncBaseResource):
            def __init__(self, config: SDKConfig):
                super().__init__(config)
                self._api = VisionVisionAPI(self._http_client)

        # For OpenAI-compatible endpoints (embeddings):
        class AsyncEmbeddingsResource(AsyncBaseResource):
            def __init__(self, config: SDKConfig):
                super().__init__(config, use_llm_url=True)
    """

    def __init__(
        self, config: "SDKConfig", *, use_llm_url: bool = False, use_audio_url: bool = False
    ):
        """
        Initialize resource with SDK configuration.

        Args:
            config: SDKConfig with api_url, llm_url, audio_url, api_key, timeout
            use_llm_url: If True, use llm_url (FastAPI LLM). Default uses api_url (Django).
            use_audio_url: If True, use audio_url (FastAPI Audio).
        """
        self._config = config
        self._factory = HTTPClientFactory(config)
        self._http_client = self._factory.create_async_client(
            use_llm_url=use_llm_url, use_audio_url=use_audio_url,
        )

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Access the underlying HTTP client for direct requests."""
        return self._http_client

    @property
    def config(self) -> "SDKConfig":
        """Access the SDK configuration."""
        return self._config


__all__ = [
    # Base classes
    "HTTPClientFactory",
    "BaseResource",
    "AsyncBaseResource",
    # Async clients
    "VisionVisionAPI",
    "CdnCdnAPI",
    "SdkKeysSdkKeysAPI",
    "ShortlinksShortlinksAPI",
    "CleanerCleanerAPI",
    "ModelsLlmModelsAPI",
    "SearchSearchAPI",
    "ImageGenImageGenAPI",
    "PaymentsPaymentsAPI",
    "ProxiesProxiesAPI",
    # Sync clients
    "SyncVisionVisionAPI",
    "SyncCdnCdnAPI",
    "SyncSdkKeysSdkKeysAPI",
    "SyncShortlinksShortlinksAPI",
    "SyncCleanerCleanerAPI",
    "SyncModelsLlmModelsAPI",
    "SyncSearchSearchAPI",
    "SyncImageGenImageGenAPI",
    "SyncPaymentsPaymentsAPI",
    "SyncProxiesProxiesAPI",
]
