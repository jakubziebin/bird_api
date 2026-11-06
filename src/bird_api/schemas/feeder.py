from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FeederCreate(BaseModel):
    feeder_id: str = Field(min_length=1, max_length=64)
    client_id: int = Field(gt=0)


class FeederResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    feeder_id: str
    client_id: int
    created_at: datetime


class VisitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    feeder_id: int
    species: str
    confidence: float
    image_path: str | None
    detected_at: datetime
