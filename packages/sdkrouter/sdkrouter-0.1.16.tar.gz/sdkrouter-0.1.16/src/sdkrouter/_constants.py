"""SDK constants and defaults."""

# Environment variable names
ENV_API_KEY = "SDKROUTER_API_KEY"
ENV_OPENROUTER_KEY = "OPENROUTER_API_KEY"
ENV_LLM_URL = "SDKROUTER_LLM_URL"
ENV_API_URL = "SDKROUTER_API_URL"
ENV_AUDIO_URL = "SDKROUTER_AUDIO_URL"

# Default URLs (production)
# llm_url: FastAPI - LLM endpoints (chat, embeddings) - OpenAI-compatible
# api_url: Django - REST API endpoints (CDN, vision, shortlinks, models, etc.)
# audio_url: FastAPI - Audio endpoints (STT, TTS) - OpenAI-compatible
DEFAULT_LLM_URL = "https://llm.sdkrouter.com/v1"
DEFAULT_API_URL = "https://api.sdkrouter.com"
DEFAULT_AUDIO_URL = "https://audio.sdkrouter.com"

# Direct provider URLs (bypass self-hosted)
OPENROUTER_URL = "https://openrouter.ai/api/v1"
OPENAI_DIRECT_URL = "https://api.openai.com/v1"

# Default settings
DEFAULT_TIMEOUT = 60.0
DEFAULT_CONNECT_TIMEOUT = 5.0
DEFAULT_MAX_RETRIES = 2
