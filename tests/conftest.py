from __future__ import annotations

import os
from collections.abc import Generator

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite://")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from bird_api.core.database import Base, get_db
from bird_api.main import bird_app


class FakeClassifier:
    def predict(self, image):
        return [
            {"label": "hoopoe", "score": 0.97},
            {"label": "kingfisher", "score": 0.02},
        ]


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        with session_factory() as session:
            yield session

    bird_app.dependency_overrides[get_db] = override_get_db
    bird_app.state.classifier = FakeClassifier()
    test_client = TestClient(bird_app)
    yield test_client
    test_client.close()

    bird_app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()
