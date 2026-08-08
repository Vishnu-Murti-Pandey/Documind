"""
Chat application service.

Coordinates:
- backend-generated conversation IDs
- document-aware conversations
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
    Generate the public conversation ID returned to the frontend.

    The PostgreSQL primary key remains separate.
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
    # Helpers
    # ============================================================

    @staticmethod
    def get_requested_paper_name(
        request: ChatRequest,
    ) -> str | None:
        """
        Extract and normalize paper_name from the request filter.
        """

        if (
            request.filter is None
            or not request.filter.paper_name
        ):
            return None

        paper_name = request.filter.paper_name.strip()

        return paper_name or None

    # ============================================================
    # Non-streaming chat
    # ============================================================

    async def chat(
        self,
        request: ChatRequest,
    ) -> ChatResponse:
        """
        Complete non-streaming chat flow.

        New conversation:
        - frontend does not send conversation_id
        - backend generates conversation_id
        - selected paper is persisted on the conversation

        Existing conversation:
        - frontend reuses the returned conversation_id
        - ConversationMemoryService verifies that the requested
          paper matches the paper stored on the conversation
        """

        conversation_id = (
            request.conversation_id
            or generate_conversation_id()
        )

        requested_paper_name = (
            self.get_requested_paper_name(
                request
            )
        )

        try:
            # --------------------------------------------------
            # Load or create the document-aware conversation
            # --------------------------------------------------

            memory_context = await self.memory.prepare(
                public_id=conversation_id,
                paper_name=requested_paper_name,
            )

            persisted_paper_name = (
                memory_context.conversation.paper_name
            )

            # --------------------------------------------------
            # Set the initial title
            # --------------------------------------------------

            if memory_context.is_new_conversation:
                await self.memory.set_initial_title(
                    conversation=(
                        memory_context.conversation
                    ),
                    user_message=request.message,
                )

            # --------------------------------------------------
            # Save user message
            # --------------------------------------------------

            await self.memory.save_user_message(
                conversation=(
                    memory_context.conversation
                ),
                content=request.message,
            )

            # --------------------------------------------------
            # Generate response
            # --------------------------------------------------

            result = await self.pipeline.ask(
                question=request.message,
                search_filter=request.filter,
                conversation_history=(
                    memory_context.llm_history
                ),
            )

            # --------------------------------------------------
            # Save assistant response
            # --------------------------------------------------

            await self.memory.save_assistant_message(
                conversation=(
                    memory_context.conversation
                ),
                content=result.answer,
                citations=result.citations,
                figures=result.figures,
                tables=result.tables,
            )

            return ChatResponse(
                conversation_id=conversation_id,
                paper_name=persisted_paper_name,
                answer=result.answer,
                citations=result.citations,
                figures=result.figures,
                tables=result.tables,
            )

        except ValueError:
            logger.exception(
                "Conversation source validation failed.",
                extra={
                    "conversation_id": conversation_id,
                    "paper_name": requested_paper_name,
                },
            )
            raise

        except Exception:
            logger.exception(
                "Non-streaming chat request failed.",
                extra={
                    "conversation_id": conversation_id,
                    "paper_name": requested_paper_name,
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
        Stream the RAG response using SSE.

        The conversation event is emitted after the conversation
        has been loaded or created so the returned paper_name is
        the value persisted in PostgreSQL.
        """

        conversation_id = (
            request.conversation_id
            or generate_conversation_id()
        )

        requested_paper_name = (
            self.get_requested_paper_name(
                request
            )
        )

        complete_answer = ""

        metadata: dict[str, Any] = {
            "citations": [],
            "figures": [],
            "tables": [],
        }

        memory_context = None

        try:
            # --------------------------------------------------
            # Load or create conversation
            # --------------------------------------------------

            memory_context = await self.memory.prepare(
                public_id=conversation_id,
                paper_name=requested_paper_name,
            )

            persisted_paper_name = (
                memory_context.conversation.paper_name
            )

            # --------------------------------------------------
            # Return the backend-generated conversation identity
            # --------------------------------------------------

            yield sse_event(
                "conversation",
                {
                    "conversation_id": conversation_id,
                    "is_new": (
                        memory_context.is_new_conversation
                    ),
                    "paper_name": persisted_paper_name,
                },
            )

            # --------------------------------------------------
            # Set title for first message
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
                conversation=(
                    memory_context.conversation
                ),
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
            # Validate output
            # --------------------------------------------------

            if not complete_answer.strip():
                raise RuntimeError(
                    "The model returned an empty answer."
                )

            # --------------------------------------------------
            # Save complete assistant answer
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
                conversation=(
                    memory_context.conversation
                ),
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
                    "paper_name": persisted_paper_name,
                },
            )

        except asyncio.CancelledError:
            logger.info(
                "Streaming client disconnected.",
                extra={
                    "conversation_id": conversation_id,
                    "paper_name": requested_paper_name,
                },
            )
            raise

        except ValueError as exc:
            logger.warning(
                "Conversation source validation failed.",
                extra={
                    "conversation_id": conversation_id,
                    "paper_name": requested_paper_name,
                },
            )

            yield sse_event(
                "error",
                {
                    "message": str(exc),
                    "conversation_id": conversation_id,
                    "paper_name": requested_paper_name,
                },
            )

            yield sse_event(
                "done",
                {
                    "status": "failed",
                    "conversation_id": conversation_id,
                    "paper_name": requested_paper_name,
                },
            )

        except Exception:
            logger.exception(
                "Streaming chat request failed.",
                extra={
                    "conversation_id": conversation_id,
                    "paper_name": requested_paper_name,
                },
            )

            yield sse_event(
                "error",
                {
                    "message": (
                        "The request could not be completed."
                    ),
                    "conversation_id": conversation_id,
                    "paper_name": requested_paper_name,
                },
            )

            yield sse_event(
                "done",
                {
                    "status": "failed",
                    "conversation_id": conversation_id,
                    "paper_name": requested_paper_name,
                },
            )