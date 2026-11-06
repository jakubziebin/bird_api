from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from bird_api.core.database import get_db
from bird_api.core.models import BirdVisit, Client, Feeder
from bird_api.schemas.feeder import FeederCreate, FeederResponse, VisitResponse

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


@router.get("/feeders/{feeder_id}/visits", response_model=list[VisitResponse])
def list_feeder_visits(
    feeder_id: str,
    db: Session = Depends(get_db),  # noqa: B008
    species: str | None = Query(default=None, min_length=1, max_length=255),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    feeder = db.scalar(select(Feeder).where(Feeder.feeder_id == feeder_id))
    if feeder is None:
        raise HTTPException(status_code=404, detail="Feeder not found")

    query = (
        select(BirdVisit)
        .where(BirdVisit.feeder_id == feeder.id)
        .order_by(desc(BirdVisit.detected_at))
        .offset(offset)
        .limit(limit)
    )
    if species is not None:
        query = query.where(BirdVisit.species == species)

    return db.scalars(query).all()
