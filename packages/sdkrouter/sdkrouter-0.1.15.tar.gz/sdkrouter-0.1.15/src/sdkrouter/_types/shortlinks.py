"""Shortlinks types."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ShortLinkCreateRequest(BaseModel):
    """Request for creating a short link."""

    url: str = Field(description="Target URL to shorten")
    custom_slug: Optional[str] = Field(default=None, description="Custom short code")
    ttl: Optional[str] = Field(default=None, description="Time to live")
    max_hits: Optional[int] = Field(default=None, description="Max redirects allowed")


class ShortLink(BaseModel):
    """Short link information."""

    code: str = Field(description="Short code")
    short_url: str = Field(description="Full short URL")
    target_url: str = Field(description="Original target URL")
    created_at: datetime = Field(description="Creation time")
    expires_at: Optional[datetime] = Field(default=None, description="Expiration time")
    hit_count: int = Field(default=0, description="Number of redirects")
    is_active: bool = Field(default=True, description="Whether link is active")
