from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import structlog
from rag.db.session import get_db
from rag.config.settings import get_settings

logger = structlog.get_logger()
router = APIRouter(tags=["health"])


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)) -> dict:
    """Legacy health check endpoint."""
    await db.execute(text("SELECT 1"))
    return {"status": "ok"}


@router.get("/health/live")
async def liveness() -> dict:
    """Liveness probe checking if application is running."""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness(db: AsyncSession = Depends(get_db)) -> dict:
    """Readiness probe checking database connection and Mistral API reachability."""
    settings = get_settings()
    errors = {}

    # 1. Check DB connectivity
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error("health_check_db_failed", error=str(e))
        errors["database"] = "unreachable"

    # 2. Check Mistral AI API reachability
    if settings.mistral_api_key:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(
                    "https://api.mistral.ai/v1/models",
                    headers={"Authorization": f"Bearer {settings.mistral_api_key}"}
                )
                if response.status_code != 200:
                    errors["mistral_api"] = f"unhealthy (status={response.status_code})"
        except Exception as e:
            logger.error("health_check_mistral_failed", error=str(e))
            errors["mistral_api"] = "unreachable"
    else:
        errors["mistral_api"] = "api_key_missing"

    if errors:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unready", "components": errors}
        )

    return {"status": "ready"}
