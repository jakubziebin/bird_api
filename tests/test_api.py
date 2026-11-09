from __future__ import annotations

from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image


def image_file() -> tuple[str, BytesIO, str]:
    image = Image.new("RGB", (10, 10), color="white")
    contents = BytesIO()
    image.save(contents, format="PNG")
    contents.seek(0)
    return "bird.png", contents, "image/png"


def create_client(client: TestClient, email: str = "test@example.com") -> dict:
    response = client.post("/api/v1/clients", json={"email": email})
    assert response.status_code == 201
    return response.json()


def create_feeder(client: TestClient, client_id: int, feeder_id: str = "feeder-001") -> dict:
    response = client.post(
        "/api/v1/feeders",
        json={"client_id": client_id, "feeder_id": feeder_id},
    )
    assert response.status_code == 201
    return response.json()


def test_create_client_and_feeder(client: TestClient) -> None:
    created_client = create_client(client)
    created_feeder = create_feeder(client, created_client["id"])

    assert created_client["email"] == "test@example.com"
    assert created_feeder["client_id"] == created_client["id"]
    assert created_feeder["feeder_id"] == "feeder-001"


def test_duplicate_client_returns_conflict(client: TestClient) -> None:
    create_client(client)

    response = client.post(
        "/api/v1/clients",
        json={"email": "test@example.com"},
    )

    assert response.status_code == 409


def test_prediction_is_stored_and_visible_in_history(client: TestClient) -> None:
    created_client = create_client(client)
    create_feeder(client, created_client["id"])

    filename, contents, content_type = image_file()
    response = client.post(
        "/api/v1/feeders/feeder-001/predict",
        files={"file": (filename, contents, content_type)},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["visit_id"] > 0
    assert body["predictions"][0] == {
        "species": "hoopoe",
        "confidence": 0.97,
    }

    history = client.get("/api/v1/feeders/feeder-001/visits")
    assert history.status_code == 200
    assert history.json()[0]["species"] == "hoopoe"


def test_prediction_for_unknown_feeder_returns_not_found(client: TestClient) -> None:
    filename, contents, content_type = image_file()
    response = client.post(
        "/api/v1/feeders/missing/predict",
        files={"file": (filename, contents, content_type)},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Feeder not found"
