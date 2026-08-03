"""
Chat API routes.
"""

from fastapi import (
    APIRouter,
    Depends,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.chat_request import ChatRequest
from app.api.schemas.chat_response import ChatResponse
from app.db.session import get_db_session
from app.services.chat_service import ChatService


router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
    session: AsyncSession = Depends(
        get_db_session
    ),
) -> ChatResponse:
    """
    Complete JSON chat endpoint.
    """

    service = ChatService(
        session=session
    )

    return await service.chat(
        request
    )


@router.post("/chat/stream")
async def stream_chat(
    request: ChatRequest,
    session: AsyncSession = Depends(
        get_db_session
    ),
) -> StreamingResponse:
    """
    SSE streaming chat endpoint.
    """

    service = ChatService(
        session=session
    )

    return StreamingResponse(
        service.stream_chat(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": (
                "no-cache, no-transform"
            ),
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )