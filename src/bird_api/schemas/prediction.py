from __future__ import annotations

from pydantic import BaseModel


class PredictionItem(BaseModel):
    species: str
    confidence: float


class PredictionResponse(BaseModel):
    predictions: list[PredictionItem]


class StoredPredictionResponse(PredictionResponse):
    visit_id: int


class BatchPredictionItem(BaseModel):
    filename: str
    species: str
    confidence: float


class BatchPredictionResponse(BaseModel):
    predictions: list[BatchPredictionItem]
