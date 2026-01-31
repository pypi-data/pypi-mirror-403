"""
Token counting utilities for LLM models.

Provides:
- Text token counting using tiktoken
- Image token estimation for vision models (OpenAI formula)
- Message-level token counting for chat completions
"""

import math
from typing import Any, Literal

import tiktoken


# ============================================================================
# Text Token Counting
# ============================================================================

# Model to encoding mapping
MODEL_ENCODINGS: dict[str, str] = {
    # GPT-4 family
    "gpt-4": "cl100k_base",
    "gpt-4o": "cl100k_base",
    "gpt-4o-mini": "cl100k_base",
    "gpt-4-turbo": "cl100k_base",
    "gpt-4-vision": "cl100k_base",
    # GPT-3.5 family
    "gpt-3.5-turbo": "cl100k_base",
    "gpt-3.5": "cl100k_base",
    # Claude family (use cl100k_base as approximation)
    "claude": "cl100k_base",
    "claude-3": "cl100k_base",
    "claude-3.5": "cl100k_base",
    # Llama family
    "llama": "cl100k_base",
    "llama-3": "cl100k_base",
    # Default
    "default": "cl100k_base",
}

# Message overhead tokens per message
MESSAGE_OVERHEAD_TOKENS = 4


class TokenCounter:
    """
    Token counting utility using tiktoken.

    Supports GPT-4, GPT-3.5, Claude (approximation), and other models.
    Caches encoders for performance.

    Example:
        counter = TokenCounter()
        tokens = counter.count("Hello, world!", model="gpt-4o")

        messages = [{"role": "user", "content": "Hi"}]
        total = counter.count_messages(messages, model="gpt-4o")
    """

    def __init__(self):
        """Initialize tokenizer with encoder cache."""
        self._encoders: dict[str, object] = {}

    def _get_encoding_name(self, model: str) -> str:
        """Get tiktoken encoding name for model."""
        model_lower = model.lower()

        # Check exact matches first
        for pattern, encoding in MODEL_ENCODINGS.items():
            if pattern in model_lower:
                return encoding

        return MODEL_ENCODINGS["default"]

    def _get_encoder(self, model: str) -> Any:
        """Get tiktoken encoder for model (cached)."""
        if model not in self._encoders:
            encoding_name = self._get_encoding_name(model)
            self._encoders[model] = tiktoken.get_encoding(encoding_name)

        return self._encoders[model]

    def count(self, text: str, model: str = "gpt-4o") -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens for
            model: Model name for encoding selection

        Returns:
            Number of tokens
        """
        if not text:
            return 0

        encoder = self._get_encoder(model)

        if encoder:
            return len(encoder.encode(text))

        # Fallback: approximate as ~4 chars per token
        return len(text) // 4 + 1

    def count_messages(
        self,
        messages: list[dict[str, str]],
        model: str = "gpt-4o"
    ) -> int:
        """
        Count total tokens in chat messages.

        Args:
            messages: List of chat messages with 'role' and 'content'
            model: Model name for encoding selection

        Returns:
            Total number of tokens including message overhead
        """
        total_tokens = 0

        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")

            # Count role and content tokens
            total_tokens += self.count(role, model)
            total_tokens += self.count(content, model)

            # Add message overhead
            total_tokens += MESSAGE_OVERHEAD_TOKENS

        return total_tokens

    def encode(self, text: str, model: str = "gpt-4o") -> list[int]:
        """
        Encode text to token IDs.

        Args:
            text: Text to encode
            model: Model name for encoding selection

        Returns:
            List of token IDs
        """
        encoder = self._get_encoder(model)

        if encoder:
            return encoder.encode(text)

        # Fallback: return empty list
        return []

    def decode(self, tokens: list[int], model: str = "gpt-4o") -> str:
        """
        Decode token IDs to text.

        Args:
            tokens: List of token IDs
            model: Model name for encoding selection

        Returns:
            Decoded text
        """
        encoder = self._get_encoder(model)

        if encoder:
            return encoder.decode(tokens)

        return ""


# ============================================================================
# Image Token Estimation (OpenAI Vision formula)
# ============================================================================

DetailMode = Literal["low", "high", "auto"]

# Token constants (OpenAI formula)
LOW_DETAIL_TOKENS = 85
HIGH_DETAIL_BASE_TOKENS = 85
HIGH_DETAIL_TILE_TOKENS = 170
TILE_SIZE = 512

# Image size limits
MAX_DIMENSION = 2048
SHORT_SIDE_TARGET = 768


def _scale_image_dimensions(width: int, height: int) -> tuple[int, int]:
    """
    Scale image dimensions according to OpenAI processing rules.

    1. Scale down if larger than 2048 on any side
    2. Scale to fit 768px on shortest side

    Args:
        width: Original width
        height: Original height

    Returns:
        Tuple of (scaled_width, scaled_height)
    """
    # Step 1: Scale down if larger than 2048
    max_dim = max(width, height)
    if max_dim > MAX_DIMENSION:
        scale = MAX_DIMENSION / max_dim
        width = int(width * scale)
        height = int(height * scale)

    # Step 2: Scale to fit 768px on shortest side
    min_dim = min(width, height)
    if min_dim > SHORT_SIDE_TARGET:
        scale = SHORT_SIDE_TARGET / min_dim
        width = int(width * scale)
        height = int(height * scale)

    return width, height


def estimate_image_tokens(
    width: int = 1024,
    height: int = 1024,
    detail: DetailMode = "high",
) -> int:
    """
    Estimate tokens for image based on OpenAI formula.

    Low detail: 85 tokens fixed
    High detail: 170 tokens per 512x512 tile + 85 base

    Args:
        width: Image width in pixels
        height: Image height in pixels
        detail: Detail mode (low/high/auto)

    Returns:
        Estimated token count

    Example:
        tokens = estimate_image_tokens(1024, 768, "high")
        print(f"Image will use ~{tokens} tokens")
    """
    # Auto mode: use high for larger images
    if detail == "auto":
        detail = "high" if max(width, height) > 512 else "low"

    if detail == "low":
        return LOW_DETAIL_TOKENS

    # High detail processing
    scaled_width, scaled_height = _scale_image_dimensions(width, height)

    # Count 512x512 tiles
    tiles_x = math.ceil(scaled_width / TILE_SIZE)
    tiles_y = math.ceil(scaled_height / TILE_SIZE)

    return HIGH_DETAIL_BASE_TOKENS + (HIGH_DETAIL_TILE_TOKENS * tiles_x * tiles_y)


def get_tile_count(width: int, height: int) -> tuple[int, int]:
    """
    Get number of 512x512 tiles for image.

    Args:
        width: Image width
        height: Image height

    Returns:
        Tuple of (tiles_x, tiles_y)
    """
    scaled_width, scaled_height = _scale_image_dimensions(width, height)
    tiles_x = math.ceil(scaled_width / TILE_SIZE)
    tiles_y = math.ceil(scaled_height / TILE_SIZE)
    return tiles_x, tiles_y


def get_optimal_detail_mode(
    width: int,
    height: int,
    max_tokens: int | None = None,
) -> DetailMode:
    """
    Determine optimal detail mode based on image size and token budget.

    Args:
        width: Image width
        height: Image height
        max_tokens: Optional maximum token budget for image

    Returns:
        Recommended detail mode ('low' or 'high')

    Example:
        mode = get_optimal_detail_mode(2048, 1536, max_tokens=500)
        # Returns 'low' if high detail would exceed 500 tokens
    """
    high_tokens = estimate_image_tokens(width, height, "high")

    # If max_tokens specified and high would exceed it, use low
    if max_tokens and high_tokens > max_tokens:
        return "low"

    # For small images, low detail is sufficient
    if max(width, height) <= 512:
        return "low"

    return "high"


# ============================================================================
# Convenience Functions
# ============================================================================

# Global tokenizer instance
_tokenizer: TokenCounter | None = None


def _get_tokenizer() -> TokenCounter:
    """Get global tokenizer instance."""
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = TokenCounter()
    return _tokenizer


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """
    Count tokens in text (convenience function).

    Args:
        text: Text to count tokens for
        model: Model name for encoding selection

    Returns:
        Number of tokens
    """
    return _get_tokenizer().count(text, model)


def count_messages_tokens(
    messages: list[dict[str, str]],
    model: str = "gpt-4o"
) -> int:
    """
    Count total tokens in chat messages (convenience function).

    Args:
        messages: List of chat messages
        model: Model name for encoding selection

    Returns:
        Total number of tokens
    """
    return _get_tokenizer().count_messages(messages, model)


__all__ = [
    # Classes
    "TokenCounter",
    # Text token functions
    "count_tokens",
    "count_messages_tokens",
    # Image token functions
    "estimate_image_tokens",
    "get_tile_count",
    "get_optimal_detail_mode",
    # Types
    "DetailMode",
    # Constants
    "LOW_DETAIL_TOKENS",
    "HIGH_DETAIL_BASE_TOKENS",
    "HIGH_DETAIL_TILE_TOKENS",
]
