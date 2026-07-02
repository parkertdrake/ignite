from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_health_reports_service():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "ignite-backend"


def test_accounts_stub_returns_list():
    response = client.get("/api/accounts")
    assert response.status_code == 200
    assert len(response.json()["accounts"]) == 2
