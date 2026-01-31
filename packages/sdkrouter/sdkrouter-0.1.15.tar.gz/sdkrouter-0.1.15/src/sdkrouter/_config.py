"""SDK configuration."""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

from ._constants import (
    DEFAULT_API_URL,
    DEFAULT_AUDIO_URL,
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_LLM_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    OPENAI_DIRECT_URL,
    OPENROUTER_URL,
)


class SDKConfig(BaseSettings):
    """SDK configuration with environment variable support.

    URLs:
        llm_url: FastAPI server for LLM endpoints (chat, embeddings) - OpenAI-compatible
        api_url: Django server for REST API endpoints (CDN, vision, shortlinks, etc.)
        audio_url: FastAPI server for Audio endpoints (STT, TTS) - OpenAI-compatible

    Production defaults:
        llm_url: https://llm.sdkrouter.com
        api_url: https://api.sdkrouter.com
        audio_url: https://audio.sdkrouter.com

    Local development (set via env vars):
        SDKROUTER_LLM_URL=http://127.0.0.1:8001
        SDKROUTER_API_URL=http://127.0.0.1:8000
        SDKROUTER_AUDIO_URL=http://127.0.0.1:8002
    """

    model_config = SettingsConfigDict(
        env_prefix="SDKROUTER_",
        env_file=".env",
        extra="ignore",
    )

    # API Keys
    api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None

    # SDKRouter URLs
    llm_url: str = DEFAULT_LLM_URL      # FastAPI: chat, embeddings (OpenAI-compatible)
    api_url: str = DEFAULT_API_URL       # Django: CDN, vision, shortlinks, etc.
    audio_url: str = DEFAULT_AUDIO_URL   # FastAPI: STT, TTS (OpenAI-compatible)

    # Direct provider URLs (bypass self-hosted)
    openrouter_direct_url: str = OPENROUTER_URL
    openai_direct_url: str = OPENAI_DIRECT_URL

    # Routing mode
    use_self_hosted: bool = True  # False = direct to OpenRouter/OpenAI

    # Timeouts
    timeout: float = DEFAULT_TIMEOUT
    connect_timeout: float = DEFAULT_CONNECT_TIMEOUT

    # Retry
    max_retries: int = DEFAULT_MAX_RETRIES


_config: Optional[SDKConfig] = None


def get_config() -> SDKConfig:
    """Get or create SDK configuration."""
    global _config
    if _config is None:
        _config = SDKConfig()
    return _config


def configure(**kwargs) -> SDKConfig:
    """Configure SDK with custom settings."""
    global _config
    _config = SDKConfig(**kwargs)
    return _config


def reset_config() -> None:
    """Reset configuration to defaults."""
    global _config
    _config = None
