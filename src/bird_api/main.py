from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from bird_api.core.database import engine
from bird_api.routes.prediction import router
from bird_api.services.ml_service import BirdClassifier


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.classifier = BirdClassifier()
    yield


bird_app = FastAPI(
    title="Bird Recognition API",
    version="1.0.0",
    lifespan=lifespan,
)

bird_app.include_router(router, prefix="/api/v1", tags=["prediction"])


@bird_app.get("/health")
def health():
    return {"status": "ok"}


@bird_app.get("/ready")
def ready():
    return {"ready": hasattr(bird_app.state, "classifier")}


@bird_app.get("/db-check")
def db_check():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    return {"status": "connected"}
