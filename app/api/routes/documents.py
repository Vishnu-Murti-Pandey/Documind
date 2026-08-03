"""
Frontend document-management routes.
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.document import (
    DocumentItem,
    DocumentListResponse,
)
from app.db.session import get_db_session
from app.services.document_service import (
    DocumentNotFoundError,
    DocumentService,
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.get(
    "",
    response_model=DocumentListResponse,
)
async def list_documents(
    page: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    session: AsyncSession = Depends(
        get_db_session
    ),
) -> DocumentListResponse:

    service = DocumentService(
        session
    )

    return await service.list_documents(
        page=page,
        limit=limit,
    )


@router.get(
    "/{paper_name}",
    response_model=DocumentItem,
)
async def get_document(
    paper_name: str,
    session: AsyncSession = Depends(
        get_db_session
    ),
) -> DocumentItem:

    service = DocumentService(
        session
    )

    try:
        return await service.get_document(
            paper_name
        )

    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        ) from exc


@router.delete(
    "/{paper_name}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    paper_name: str,
    session: AsyncSession = Depends(
        get_db_session
    ),
) -> Response:

    service = DocumentService(
        session
    )

    try:
        await service.delete_document(
            paper_name
        )

        return Response(
            status_code=status.HTTP_204_NO_CONTENT
        )

    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        ) from exc