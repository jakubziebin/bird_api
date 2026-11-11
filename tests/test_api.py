from __future__ import annotations

from io import BytesIO
from typing import Any, Final


from fastapi.testclient import TestClient
from PIL import Image


TEST_EMAIL: Final[str] = "test@example.com"
TEST_FEEDER_ID: Final[str] = "feeder-001"

type ImageFile = tuple[str, BytesIO, str]  # filename, contents, content_type


def image_file() -> ImageFile:
    image = Image.new("RGB", (10, 10), color="white")
    contents = BytesIO()
    image.save(contents, format="PNG")
    contents.seek(0)
    return "bird.png", contents, "image/png"


def create_client(client: TestClient, email: str = TEST_EMAIL) -> dict:
    response = client.post("/api/v1/clients", json={"email": email})
    assert response.status_code == 201
    return response.json()


def create_feeder(
    client: TestClient, client_id: int, feeder_id: str = TEST_FEEDER_ID
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/feeders",
        json={"client_id": client_id, "feeder_id": feeder_id},
    )
    assert response.status_code == 201
    return response.json()


def test_create_client_and_feeder(client: TestClient) -> None:
    # ARRANGE & ACT
    created_client = create_client(client)
    created_feeder = create_feeder(client, created_client["id"])

    # ASSERT
    assert created_client["email"] == TEST_EMAIL
    assert created_feeder["client_id"] == created_client["id"]
    assert created_feeder["feeder_id"] == TEST_FEEDER_ID


def test_duplicate_client_returns_conflict(client: TestClient) -> None:
    # ARRANGE
    create_client(client)

    # ACT
    response = client.post(
        "/api/v1/clients",
        json={"email": "test@example.com"},
    )

    # ASSERT
    assert response.status_code == 409


def test_prediction_is_stored_and_visible_in_history(client: TestClient) -> None:
    # ARRANGE
    created_client = create_client(client)
    create_feeder(client, created_client["id"])

    filename, contents, content_type = image_file()

    # ACT
    response = client.post(
        "/api/v1/feeders/feeder-001/predict",
        files={"file": (filename, contents, content_type)},
    )
    body = response.json()

    history = client.get("/api/v1/feeders/feeder-001/visits")

    # ASSERT
    assert response.status_code == 201
    assert body["visit_id"] > 0
    assert body["predictions"][0] == {
        "species": "hoopoe",
        "confidence": 0.97,
    }
    assert history.status_code == 200
    assert history.json()[0]["species"] == "hoopoe"


def test_prediction_for_unknown_feeder_returns_not_found(client: TestClient) -> None:
    # ARRANGE
    filename, contents, content_type = image_file()

    # ACT
    response = client.post(
        "/api/v1/feeders/missing/predict",
        files={"file": (filename, contents, content_type)},
    )

    # ASSERT
    assert response.status_code == 404
    assert response.json()["detail"] == "Feeder not found"
