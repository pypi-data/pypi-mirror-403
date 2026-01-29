"""API Key models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ApiKeyData(BaseModel):
    """API key information."""

    guid: str
    name: str
    key_prefix: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None


class ApiKeyCreateResponse(BaseModel):
    """Response from creating an API key."""

    guid: str
    key: str  # Full key, only shown once
