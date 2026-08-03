"""
Chat application service.

Coordinates:
- backend-generated conversation IDs
- conversation memory
- RAG generation
- assistant response persistence
- SSE formatting
"""

import asyncio
import logging
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.chat_request import ChatRequest
from app.api.schemas.chat_response import ChatResponse
from app.api.sse import sse_event
from app.config import CONVERSATION_HISTORY_LIMIT
from app.generation.rag_pipeline import RAGPipeline
from app.services.conversation_memory import (
    ConversationMemoryService,
)


logger = logging.getLogger(__name__)


def generate_conversation_id() -> str:
    """
    Generate a frontend-safe public conversation identifier.

    The internal PostgreSQL primary key remains separate.
    """

    return str(uuid.uuid4())


class ChatService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.pipeline = RAGPipeline()

        self.memory = ConversationMemoryService(
            session=session,
            history_limit=CONVERSATION_HISTORY_LIMIT,
        )

    # ============================================================
    # Non-streaming chat
    # ============================================================

    async def chat(
        self,
        request: ChatRequest,
    ) -> ChatResponse:
        """
        Complete non-streaming chat flow.

        For a new chat:
        - request.conversation_id is None
        - backend generates the conversation ID

        For an existing chat:
        - frontend sends the previously returned conversation ID
        """

        conversation_id = (
            request.conversation_id
            or generate_conversation_id()
        )

        # --------------------------------------------------
        # Load or create the conversation
        # --------------------------------------------------

        memory_context = await self.memory.prepare(
            public_id=conversation_id,
        )

        # --------------------------------------------------
        # Set the title for a new conversation
        # --------------------------------------------------

        if memory_context.is_new_conversation:
            await self.memory.set_initial_title(
                conversation=memory_context.conversation,
                user_message=request.message,
            )

        # --------------------------------------------------
        # Save the current user message
        # --------------------------------------------------

        await self.memory.save_user_message(
            conversation=memory_context.conversation,
            content=request.message,
        )

        try:
            # --------------------------------------------------
            # Generate the answer using previous history
            # --------------------------------------------------

            result = await self.pipeline.ask(
                question=request.message,
                search_filter=request.filter,
                conversation_history=(
                    memory_context.llm_history
                ),
            )

            # --------------------------------------------------
            # Save the assistant response
            # --------------------------------------------------

            await self.memory.save_assistant_message(
                conversation=memory_context.conversation,
                content=result.answer,
                citations=result.citations,
                figures=result.figures,
                tables=result.tables,
            )

            return ChatResponse(
                conversation_id=conversation_id,
                answer=result.answer,
                citations=result.citations,
                figures=result.figures,
                tables=result.tables,
            )

        except Exception:
            logger.exception(
                "Non-streaming chat request failed.",
                extra={
                    "conversation_id": conversation_id,
                },
            )

            raise

    # ============================================================
    # Streaming chat
    # ============================================================

    async def stream_chat(
        self,
        request: ChatRequest,
    ) -> AsyncGenerator[str, None]:
        """
        Streaming chat flow.

        The conversation ID is generated once and sent to the
        frontend before token streaming begins.

        The full answer is accumulated and saved after generation.
        """

        conversation_id = (
            request.conversation_id
            or generate_conversation_id()
        )

        complete_answer = ""

        metadata: dict[str, Any] = {
            "citations": [],
            "figures": [],
            "tables": [],
        }

        try:
            # --------------------------------------------------
            # Send the conversation ID immediately
            # --------------------------------------------------

            yield sse_event(
                "conversation",
                {
                    "conversation_id": conversation_id,
                    "is_new": (
                        request.conversation_id is None
                    ),
                },
            )

            # --------------------------------------------------
            # Load or create the conversation
            # --------------------------------------------------

            memory_context = await self.memory.prepare(
                public_id=conversation_id,
            )

            # --------------------------------------------------
            # Create initial conversation title
            # --------------------------------------------------

            if memory_context.is_new_conversation:
                await self.memory.set_initial_title(
                    conversation=(
                        memory_context.conversation
                    ),
                    user_message=request.message,
                )

            # --------------------------------------------------
            # Save current user message
            # --------------------------------------------------

            await self.memory.save_user_message(
                conversation=memory_context.conversation,
                content=request.message,
            )

            yield sse_event(
                "status",
                {
                    "stage": "memory",
                    "message": (
                        "Loading conversation context..."
                    ),
                },
            )

            # --------------------------------------------------
            # Stream RAG events
            # --------------------------------------------------

            async for event in self.pipeline.stream_events(
                question=request.message,
                search_filter=request.filter,
                conversation_history=(
                    memory_context.llm_history
                ),
            ):
                event_type = event["type"]
                event_data = event["data"]

                if event_type == "token":
                    token = event_data.get(
                        "content",
                        "",
                    )

                    complete_answer += token

                elif event_type == "metadata":
                    metadata = event_data

                yield sse_event(
                    event_type,
                    event_data,
                )

            # --------------------------------------------------
            # Validate generated answer
            # --------------------------------------------------

            if not complete_answer.strip():
                raise RuntimeError(
                    "The model returned an empty answer."
                )

            # --------------------------------------------------
            # Persist assistant response
            # --------------------------------------------------

            yield sse_event(
                "status",
                {
                    "stage": "saving",
                    "message": (
                        "Saving conversation..."
                    ),
                },
            )

            await self.memory.save_assistant_message(
                conversation=memory_context.conversation,
                content=complete_answer,
                citations=metadata.get(
                    "citations",
                    [],
                ),
                figures=metadata.get(
                    "figures",
                    [],
                ),
                tables=metadata.get(
                    "tables",
                    [],
                ),
            )

            # --------------------------------------------------
            # Complete stream
            # --------------------------------------------------

            yield sse_event(
                "done",
                {
                    "status": "completed",
                    "conversation_id": conversation_id,
                },
            )

        except asyncio.CancelledError:
            logger.info(
                "Streaming client disconnected.",
                extra={
                    "conversation_id": conversation_id,
                },
            )

            raise

        except Exception:
            logger.exception(
                "Streaming chat request failed.",
                extra={
                    "conversation_id": conversation_id,
                },
            )

            yield sse_event(
                "error",
                {
                    "message": (
                        "The request could not be completed."
                    ),
                    "conversation_id": conversation_id,
                },
            )

            yield sse_event(
                "done",
                {
                    "status": "failed",
                    "conversation_id": conversation_id,
                },
            )