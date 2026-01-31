"""CDN types."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CDNUploadRequest(BaseModel):
    """Request for CDN file upload."""

    filename: Optional[str] = Field(default=None, description="Original filename")
    content_type: Optional[str] = Field(default=None, description="MIME type")
    ttl: str = Field(default="30d", description="Time to live (e.g., '7d', '30d', '1y')")


class CDNFile(BaseModel):
    """CDN file information."""

    uuid: str = Field(description="Unique file identifier")
    filename: str = Field(description="Original filename")
    content_type: str = Field(description="MIME type")
    size_bytes: int = Field(description="File size in bytes")
    url: str = Field(description="Full URL to access file")
    expires_at: Optional[datetime] = Field(default=None, description="Expiration time")
    created_at: Optional[datetime] = Field(default=None, description="Upload time")
