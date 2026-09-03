import pytest
from starlette.testclient import TestClient
from api.webhook import app


def test_health_check():
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"


def test_mini_app_served():
    client = TestClient(app)
    response = client.get("/app")
    assert response.status_code == 200
    assert "Career Fit Preferences" in response.text
    assert "sector-group" in response.text


def test_webhook_secret_rejection(monkeypatch):
    monkeypatch.setattr("api.webhook.WEBHOOK_SECRET", "super_secret_token_123")
    client = TestClient(app)

    # Missing or invalid secret header
    response = client.post(
        "/api/webhook",
        json={"update_id": 12345},
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong_secret"},
    )
    assert response.status_code == 403


def test_webhook_invalid_json(monkeypatch):
    monkeypatch.setattr("api.webhook.WEBHOOK_SECRET", "")
    client = TestClient(app)
    response = client.post(
        "/api/webhook",
        content="not valid json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
