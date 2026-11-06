from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from bird_api.core.database import get_db
from bird_api.core.models import Client, Feeder
from bird_api.schemas.feeder import FeederCreate, FeederResponse

router = APIRouter()


@router.post(
    "/feeders",
    response_model=FeederResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_feeder(
    payload: FeederCreate,
    db: Session = Depends(get_db),  # noqa: B008
):
    client = db.scalar(select(Client).where(Client.id == payload.client_id))
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    feeder = Feeder(
        feeder_id=payload.feeder_id,
        client_id=payload.client_id,
    )
    db.add(feeder)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Feeder already exists") from None

    db.refresh(feeder)
    return feeder
