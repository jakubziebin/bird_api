from __future__ import annotations

from io import BytesIO
from typing import Final

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from bird_api.core.database import get_db
from bird_api.core.models import BirdVisit, Feeder
from bird_api.schemas.prediction import (
    BatchPredictionResponse,
    PredictionResponse,
    StoredPredictionResponse,
)

ALLOWED_TYPES: Final[set[str]] = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE: Final[int] = 10 * 1024 * 1024  # 10 MB
FILE_TOO_LARGE_ERROR_MSG: Final[str] = "File too large"

router = APIRouter()


async def classify_file(request: Request, file: UploadFile):
    """
    Classify an uploaded image file using the BirdClassifier.

    Args:
        request: The FastAPI request object.
        file: The uploaded image file.

    Returns:
        A list of predictions, where each prediction is a dictionary containing
        the label and score of the predicted species.

    Raises:
        HTTPException(status_code=400): If the uploaded file is not an allowed image type.
        HTTPException(status_code=413): If the uploaded file exceeds the maximum allowed size.
    """

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported image type",
        )

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=FILE_TOO_LARGE_ERROR_MSG,
        )

    image = Image.open(BytesIO(contents))

    classifier = request.app.state.classifier
    return classifier.predict(image)


def format_predictions(prediction: list[dict], max_results: int = 5) -> list[dict]:
    return [
        {"species": item["label"], "confidence": item["score"]}
        for item in prediction[:max_results]
    ]


@router.post("/predict", response_model=PredictionResponse)
async def predict(request: Request, file: UploadFile):
    """Predict the species of a bird in an uploaded image file."""
    
    prediction = await classify_file(request, file)

    return {"predictions": format_predictions(prediction)}


@router.post(
    "/feeders/{feeder_id}/predict",
    response_model=StoredPredictionResponse,
    status_code=201,
)
async def predict_and_store(
    feeder_id: str,
    request: Request,
    file: UploadFile,
    db: Session = Depends(get_db),
):
    feeder = db.scalar(select(Feeder).where(Feeder.feeder_id == feeder_id))
    if feeder is None:
        raise HTTPException(status_code=404, detail="Feeder not found")

    prediction = await classify_file(request, file)
    best_prediction = prediction[0]
    visit = BirdVisit(
        feeder_id=feeder.id,
        species=best_prediction["label"],
        confidence=best_prediction["score"],
    )
    db.add(visit)
    db.commit()
    db.refresh(visit)

    return {
        "visit_id": visit.id,
        "predictions": format_predictions(prediction),
    }


@router.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
)
async def predict_batch(
    request: Request,
    files: list[UploadFile],
):
    classifier = request.app.state.classifier

    results = []

    for file in files:
        if file.content_type not in ALLOWED_TYPES:
            continue

        contents = await file.read()

        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=FILE_TOO_LARGE_ERROR_MSG,
            )

        image = Image.open(BytesIO(contents))

        prediction = classifier.predict(image)
        best = prediction[0]

        results.append(
            {
                "filename": file.filename,
                "species": best["label"],
                "confidence": best["score"],
            }
        )

    return {"predictions": results}
