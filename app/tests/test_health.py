from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200() -> None:
    response = client.get("/health")

    assert response.status_code == 200


def test_health_returns_expected_payload() -> None:
    response = client.get("/health")
    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["llm_provider"] == "mock"
    assert payload["database"] in {"connected", "disconnected"}
