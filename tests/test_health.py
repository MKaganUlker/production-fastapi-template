from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_healthy_status() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "Production FastAPI Template",
        "version": "0.1.0",
        "environment": "local",
    }


def test_openapi_schema_is_available() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Production FastAPI Template"
    assert response.json()["info"]["version"] == "0.1.0"


def test_root_returns_service_links() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Production FastAPI Template",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
