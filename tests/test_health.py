from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.main import app

client = TestClient(app)


def test_health_check_returns_healthy_status() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "Production FastAPI Template",
        "version": "0.2.0",
        "environment": "local",
    }


def test_root_returns_service_links() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Production FastAPI Template",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


def test_openapi_schema_is_available() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Production FastAPI Template"
    assert response.json()["info"]["version"] == "0.2.0"


def test_readiness_check_returns_ready_when_database_is_available() -> None:
    session = AsyncMock(spec=AsyncSession)

    result = MagicMock()
    result.scalar_one.return_value = 1

    session.execute.return_value = result

    async def override_get_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db_session] = override_get_db_session

    try:
        response = client.get("/api/v1/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "available",
    }

    session.execute.assert_awaited_once()
    result.scalar_one.assert_called_once_with()


def test_readiness_check_returns_503_when_database_is_unavailable() -> None:
    session = AsyncMock(spec=AsyncSession)

    session.execute.side_effect = OperationalError(
        statement="SELECT 1",
        params=None,
        orig=Exception("Database connection failed"),
    )

    async def override_get_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db_session] = override_get_db_session

    try:
        response = client.get("/api/v1/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Database is unavailable",
    }

    session.execute.assert_awaited_once()
