"""AI Model configuration models."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class AIModelResponse(BaseModel):
    """AI model configuration."""

    guid: str
    provider: str
    is_active: bool

    # Main model
    model_id: str
    display_name: str
    quality_ranking: str
    speed_ranking: str

    # Mini model
    mini_model_id: str
    mini_display_name: str
    mini_quality_ranking: str
    mini_speed_ranking: str

    # Ordering
    sort_order: int
