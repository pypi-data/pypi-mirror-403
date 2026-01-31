"""Vision types."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class VisionAnalyzeRequest(BaseModel):
    """Request for vision analysis."""

    image: Optional[str] = Field(default=None, description="Base64 encoded image")
    image_url: Optional[str] = Field(default=None, description="URL of image to analyze")
    prompt: Optional[str] = Field(default=None, description="Custom analysis prompt")
    model: Optional[str] = Field(default=None, description="Vision model to use")
    model_quality: Literal["fast", "balanced", "best"] = Field(
        default="balanced", description="Quality preset for model selection"
    )
    fetch_image: bool = Field(default=True, description="Whether to fetch and store image")


class VisionAnalyzeResponse(BaseModel):
    """Response from vision analysis."""

    extracted_text: str = Field(description="Text extracted from the image")
    description: str = Field(description="Description of the image content")
    language: str = Field(description="Detected language")
    model: str = Field(description="Model used for analysis")
    cost_usd: float = Field(description="Cost of the analysis in USD")
    cached: bool = Field(default=False, description="Whether result was from cache")
