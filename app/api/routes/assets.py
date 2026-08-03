"""
Asset delivery routes.

The frontend uses stable FastAPI URLs.
A fresh MinIO presigned URL is generated for every request.
"""

import asyncio
from functools import lru_cache

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.responses import RedirectResponse
from minio.error import S3Error

from app.storage.minio_storage import MinioStorage


router = APIRouter(
    prefix="/assets",
    tags=["Assets"],
)


@lru_cache
def get_minio_storage() -> MinioStorage:
    """
    Create MinIOStorage lazily on the first asset request.

    This prevents FastAPI from crashing during module import
    if MinIO is temporarily unavailable.
    """

    return MinioStorage()


@router.get("/{object_path:path}")
async def get_asset(
    object_path: str,
    storage: MinioStorage = Depends(get_minio_storage),
) -> RedirectResponse:

    try:
        presigned_url = await asyncio.to_thread(
            storage.get_presigned_url,
            object_path,
        )

        return RedirectResponse(
            url=presigned_url,
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    except S3Error as exc:

        if exc.code in {
            "NoSuchKey",
            "NoSuchBucket",
            "NoSuchObject",
        }:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found.",
            ) from exc

        if exc.code in {
            "AccessDenied",
            "InvalidAccessKeyId",
            "SignatureDoesNotMatch",
        }:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Asset storage authentication failed.",
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Asset storage request failed.",
        ) from exc