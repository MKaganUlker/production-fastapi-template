import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])

DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]


class HealthResponse(BaseModel):
    status: Literal["healthy"]
    service: str
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    status: Literal["ready"]
    database: Literal["available"]


@router.get(
    "",
    response_model=HealthResponse,
    summary="Check application health",
)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Check application readiness",
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Database is unavailable",
        }
    },
)
async def readiness_check(session: DatabaseSession) -> ReadinessResponse:
    try:
        result = await session.execute(text("SELECT 1"))

        if result.scalar_one() != 1:
            raise RuntimeError("Unexpected database readiness result")
    except SQLAlchemyError as exc:
        logger.exception("Database readiness check failed")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from exc

    return ReadinessResponse(
        status="ready",
        database="available",
    )
