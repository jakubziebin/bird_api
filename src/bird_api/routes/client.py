from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from bird_api.core.database import get_db
from bird_api.core.models import Client
from bird_api.schemas.client import ClientCreate, ClientResponse

router = APIRouter()


@router.post(
    "/clients",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_client(
    payload: ClientCreate,
    db: Session = Depends(get_db),  # noqa: B008
):
    client = Client(email=payload.email)
    db.add(client)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Client already exists") from None

    db.refresh(client)
    return client
