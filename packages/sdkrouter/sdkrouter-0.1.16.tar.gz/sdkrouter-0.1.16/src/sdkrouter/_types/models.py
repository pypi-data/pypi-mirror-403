"""Model types."""

from typing import Optional

from pydantic import BaseModel, Field


class ModelPricing(BaseModel):
    """Model pricing information."""

    prompt: float = Field(description="Cost per 1M input tokens")
    completion: float = Field(description="Cost per 1M output tokens")
    image: Optional[float] = Field(default=None, description="Cost per image")


class ModelInfo(BaseModel):
    """LLM model information."""

    id: str = Field(description="Model identifier")
    name: str = Field(description="Display name")
    provider: str = Field(description="Provider name")
    context_length: int = Field(description="Max context length")
    pricing: ModelPricing = Field(description="Pricing information")
    supports_vision: bool = Field(default=False, description="Supports image input")
    supports_tools: bool = Field(default=False, description="Supports function calling")
    supports_json: bool = Field(default=False, description="Supports JSON mode")
