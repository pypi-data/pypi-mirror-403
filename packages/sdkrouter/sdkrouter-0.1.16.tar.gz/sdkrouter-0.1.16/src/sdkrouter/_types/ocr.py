"""OCR types."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class OCRRequest(BaseModel):
    """Request for OCR text extraction."""

    image: Optional[str] = Field(default=None, description="Base64 encoded image")
    image_url: Optional[str] = Field(default=None, description="URL of image")
    mode: Literal["tiny", "small", "base", "maximum"] = Field(
        default="base", description="OCR model size/quality"
    )


class OCRResponse(BaseModel):
    """Response from OCR extraction."""

    text: str = Field(description="Extracted text")
    model: str = Field(description="Model used")
    cost_usd: float = Field(description="Cost in USD")
    cached: bool = Field(default=False, description="Whether result was from cache")
