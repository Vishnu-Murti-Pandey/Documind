"""
Conversation memory service.

Responsibilities:
- Get or create conversations
- Load recent conversation history
- Save user messages
- Save assistant messages
- Convert database messages into LLM-compatible history
- Manage database transactions
"""

from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chat_message import (
    ChatMessage,
    MessageRole,
)
from app.db.models.conversation import Conversation
from app.repositories.chat_message_repository import (
    ChatMessageRepository,
)
from app.repositories.conversation_repository import (
    ConversationRepository,
)


@dataclass(slots=True)
class ConversationMemoryContext:
    """
    Prepared memory state for one incoming chat request.
    """

    conversation: Conversation

    history: list[ChatMessage]

    llm_history: list[dict[str, str]]

    is_new_conversation: bool


class ConversationMemoryService:
    """
    Coordinates conversation and message persistence.

    Repositories perform queries.
    This service controls transactions and application behavior.
    """

    def __init__(
        self,
        session: AsyncSession,
        history_limit: int = 10,
    ) -> None:
        self.session = session

        self.conversation_repository = (
            ConversationRepository(session)
        )

        self.message_repository = (
            ChatMessageRepository(session)
        )

        self.history_limit = history_limit

    # ============================================================
    # Conversation preparation
    # ============================================================

    async def prepare(
        self,
        public_id: str,
        paper_name: str | None = None,
    ) -> ConversationMemoryContext:
        """
        Get or create a conversation and load its recent history.

        This method does not save the current user message.
        Therefore, the returned history contains only previous turns.
        """

        conversation, is_new = (
            await self.conversation_repository.get_or_create(
                public_id=public_id,
                paper_name=paper_name,
            )
        )

        if (
            not is_new
            and paper_name
            and conversation.paper_name
            and conversation.paper_name != paper_name
        ):
            raise ValueError(
                "This conversation is associated with a different document."
            )

        if (
            not is_new
            and paper_name
            and not conversation.paper_name
        ):
            await self.conversation_repository.update_paper_name(
                conversation=conversation,
                paper_name=paper_name,
            )

        await self.session.commit()

        await self.session.refresh(
            conversation
        )

        messages = (
            await self.message_repository.list_recent(
                conversation_id=conversation.id,
                limit=self.history_limit,
            )
        )

        llm_history = [
            {
                "role": message.role.value,
                "content": message.content,
            }
            for message in messages
        ]

        return ConversationMemoryContext(
            conversation=conversation,
            is_new_conversation=is_new,
            messages=messages,
            llm_history=llm_history,
        )

    # ============================================================
    # User messages
    # ============================================================

    async def save_user_message(
        self,
        conversation: Conversation,
        content: str,
        retrieval_query: str | None = None,
    ) -> ChatMessage:
        """
        Save the current user message.

        original_query:
            Exact text submitted by the user.

        retrieval_query:
            Standalone rewritten query used for RAG retrieval.
            For now, this can be the same as content or None.
        """

        content = content.strip()

        if not content:
            raise ValueError(
                "User message cannot be empty."
            )

        try:
            message = (
                await self.message_repository.create_user_message(
                    conversation_id=conversation.id,
                    content=content,
                    original_query=content,
                    retrieval_query=retrieval_query,
                )
            )

            await self.conversation_repository.touch(
                conversation
            )

            await self.session.commit()

            await self.session.refresh(
                message
            )

            return message

        except Exception:
            await self.session.rollback()
            raise

    # ============================================================
    # Assistant messages
    # ============================================================

    async def save_assistant_message(
        self,
        conversation: Conversation,
        content: str,
        citations: list[Any] | None = None,
        figures: list[Any] | None = None,
        tables: list[Any] | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
    ) -> ChatMessage:
        """
        Save the complete assistant response and its RAG metadata.
        """

        content = content.strip()

        if not content:
            raise ValueError(
                "Assistant message cannot be empty."
            )

        citation_data = self._serialize_items(
            citations
        )

        figure_data = self._serialize_items(
            figures
        )

        table_data = self._serialize_items(
            tables
        )

        try:
            message = (
                await self.message_repository.create_assistant_message(
                    conversation_id=conversation.id,
                    content=content,
                    citations=citation_data,
                    figures=figure_data,
                    tables=table_data,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
            )

            await self.conversation_repository.touch(
                conversation
            )

            await self.session.commit()

            await self.session.refresh(
                message
            )

            return message

        except Exception:
            await self.session.rollback()
            raise

    # ============================================================
    # Conversation history
    # ============================================================

    async def load_recent_history(
        self,
        conversation: Conversation,
        limit: int | None = None,
    ) -> list[ChatMessage]:
        """
        Load recent messages in chronological order.
        """

        return await self.message_repository.list_recent(
            conversation_id=conversation.id,
            limit=limit or self.history_limit,
        )

    async def load_llm_history(
        self,
        conversation: Conversation,
        limit: int | None = None,
    ) -> list[dict[str, str]]:
        """
        Load conversation history in OpenAI-compatible format.
        """

        messages = await self.load_recent_history(
            conversation=conversation,
            limit=limit,
        )

        return self.to_llm_history(
            messages
        )

    # ============================================================
    # Title
    # ============================================================

    async def set_initial_title(
        self,
        conversation: Conversation,
        user_message: str,
        max_length: int = 80,
    ) -> Conversation:
        """
        Set a simple initial title from the first user message.

        An LLM-based title generator can replace this later.
        """

        if conversation.title:
            return conversation

        title = " ".join(
            user_message.strip().split()
        )

        if len(title) > max_length:
            title = (
                title[: max_length - 3].rstrip()
                + "..."
            )

        try:
            conversation = (
                await self.conversation_repository.update_title(
                    conversation=conversation,
                    title=title,
                )
            )

            await self.session.commit()

            return conversation

        except Exception:
            await self.session.rollback()
            raise

    # ============================================================
    # Serialization helpers
    # ============================================================

    @staticmethod
    def to_llm_history(
        messages: list[ChatMessage],
    ) -> list[dict[str, str]]:
        """
        Convert ORM message objects into LLM-compatible messages.

        Example:

        [
            {
                "role": "user",
                "content": "Explain attention."
            },
            {
                "role": "assistant",
                "content": "Attention is..."
            }
        ]
        """

        history: list[dict[str, str]] = []

        for message in messages:
            if message.role not in {
                MessageRole.USER,
                MessageRole.ASSISTANT,
                MessageRole.SYSTEM,
            }:
                continue

            history.append(
                {
                    "role": message.role.value,
                    "content": message.content,
                }
            )

        return history

    @staticmethod
    def _serialize_items(
        items: list[Any] | None,
    ) -> list[dict[str, Any]]:
        """
        Convert Pydantic models or dictionaries into JSON-safe dicts.
        """

        if not items:
            return []

        serialized: list[dict[str, Any]] = []

        for item in items:
            if hasattr(item, "model_dump"):
                serialized.append(
                    item.model_dump(
                        mode="json"
                    )
                )

            elif isinstance(item, dict):
                serialized.append(item)

            else:
                raise TypeError(
                    "Conversation metadata must contain "
                    "Pydantic models or dictionaries."
                )

        return serialized