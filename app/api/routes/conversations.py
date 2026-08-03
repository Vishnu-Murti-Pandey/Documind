"""
Frontend-facing conversation management routes.
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

from app.api.schemas.conversation import (
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationMessagesResponse,
    ConversationUpdateRequest,
)
from app.db.session import get_db_session
from app.services.conversation_service import (
    ConversationNotFoundError,
    ConversationService,
)


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


@router.get(
    "",
    response_model=ConversationListResponse,
)
async def list_conversations(
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
) -> ConversationListResponse:

    service = ConversationService(
        session=session
    )

    return await service.list_conversations(
        page=page,
        limit=limit,
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetailResponse,
)
async def get_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(
        get_db_session
    ),
) -> ConversationDetailResponse:

    service = ConversationService(
        session=session
    )

    try:
        return await service.get_conversation(
            public_id=conversation_id
        )

    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        ) from exc


@router.get(
    "/{conversation_id}/messages",
    response_model=ConversationMessagesResponse,
)
async def get_conversation_messages(
    conversation_id: str,
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
) -> ConversationMessagesResponse:

    service = ConversationService(
        session=session
    )

    try:
        return await service.get_messages(
            public_id=conversation_id,
            page=page,
            limit=limit,
        )

    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        ) from exc


@router.patch(
    "/{conversation_id}",
    response_model=ConversationDetailResponse,
)
async def rename_conversation(
    conversation_id: str,
    request: ConversationUpdateRequest,
    session: AsyncSession = Depends(
        get_db_session
    ),
) -> ConversationDetailResponse:

    service = ConversationService(
        session=session
    )

    try:
        return await service.rename_conversation(
            public_id=conversation_id,
            title=request.title,
        )

    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        ) from exc


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(
        get_db_session
    ),
) -> Response:

    service = ConversationService(
        session=session
    )

    try:
        await service.delete_conversation(
            public_id=conversation_id
        )

        return Response(
            status_code=status.HTTP_204_NO_CONTENT
        )

    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        ) from exc