"""
Application health routes.
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("")
async def health():
    return {
        "status": "ok",
    }


@router.get("/database")
async def database_health(
    session: AsyncSession = Depends(
        get_db_session
    ),
):
    try:
        result = await session.execute(
            text("SELECT 1")
        )

        result.scalar_one()

        return {
            "status": "ok",
            "database": "connected",
        }

    except Exception as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail="Database is unavailable.",
        ) from exc