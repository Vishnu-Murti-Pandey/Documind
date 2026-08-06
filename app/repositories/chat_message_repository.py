"""
Chat message repository.

Contains all database operations related to chat messages.
"""

from uuid import UUID

from sqlalchemy import (
    and_,
    delete,
    func,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.message_cursor import MessageCursor

from app.db.models.chat_message import (
    ChatMessage,
    MessageRole,
)


class ChatMessageRepository:

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def create(
        self,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
        original_query: str | None = None,
        retrieval_query: str | None = None,
        citations: list[dict] | None = None,
        figures: list[dict] | None = None,
        tables: list[dict] | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
    ) -> ChatMessage:

        content = content.strip()

        if not content:
            raise ValueError(
                "Message content cannot be empty."
            )

        message = ChatMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            original_query=original_query,
            retrieval_query=retrieval_query,
            citations=citations or [],
            figures=figures or [],
            tables=tables or [],
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        self.session.add(message)

        await self.session.flush()

        return message

    async def create_user_message(
        self,
        conversation_id: UUID,
        content: str,
        original_query: str | None = None,
        retrieval_query: str | None = None,
    ) -> ChatMessage:

        return await self.create(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
            original_query=(
                original_query or content
            ),
            retrieval_query=retrieval_query,
        )

    async def create_assistant_message(
        self,
        conversation_id: UUID,
        content: str,
        citations: list[dict] | None = None,
        figures: list[dict] | None = None,
        tables: list[dict] | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
    ) -> ChatMessage:

        return await self.create(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=content,
            citations=citations,
            figures=figures,
            tables=tables,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    async def get_by_id(
        self,
        message_id: UUID,
    ) -> ChatMessage | None:

        return await self.session.get(
            ChatMessage,
            message_id,
        )

    async def list_recent(
        self,
        conversation_id: UUID,
        limit: int = 10,
    ) -> list[ChatMessage]:

        statement = (
            select(ChatMessage)
            .where(
                ChatMessage.conversation_id
                == conversation_id
            )
            .order_by(
                ChatMessage.created_at.desc(),
                ChatMessage.id.desc(),
            )
            .limit(limit)
        )

        result = await self.session.execute(
            statement
        )

        messages = list(
            result.scalars().all()
        )

        messages.reverse()

        return messages

    async def list_paginated(
        self,
        conversation_id: UUID,
        page: int = 0,
        limit: int = 20,
    ) -> tuple[list[ChatMessage], int]:
        """
        Return messages in chronological order.

        Page 0 returns the earliest messages. This works well for a
        first frontend implementation. Later, cursor pagination can
        be added for very large conversations.
        """

        offset = page * limit

        count_statement = select(
            func.count(ChatMessage.id)
        ).where(
            ChatMessage.conversation_id
            == conversation_id
        )

        count_result = await self.session.execute(
            count_statement
        )

        total = int(
            count_result.scalar_one()
        )

        statement = (
            select(ChatMessage)
            .where(
                ChatMessage.conversation_id
                == conversation_id
            )
            .order_by(
                ChatMessage.created_at.asc(),
                ChatMessage.id.asc(),
            )
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(
            statement
        )

        messages = list(
            result.scalars().all()
        )

        return messages, total

    async def list_all(
        self,
        conversation_id: UUID,
    ) -> list[ChatMessage]:

        statement = (
            select(ChatMessage)
            .where(
                ChatMessage.conversation_id
                == conversation_id
            )
            .order_by(
                ChatMessage.created_at.asc(),
                ChatMessage.id.asc(),
            )
        )

        result = await self.session.execute(
            statement
        )

        return list(
            result.scalars().all()
        )

    async def count(
        self,
        conversation_id: UUID,
    ) -> int:

        statement = select(
            func.count(ChatMessage.id)
        ).where(
            ChatMessage.conversation_id
            == conversation_id
        )

        result = await self.session.execute(
            statement
        )

        return int(
            result.scalar_one()
        )

    async def delete(
        self,
        message: ChatMessage,
    ) -> None:

        await self.session.delete(
            message
        )

        await self.session.flush()

    async def delete_by_conversation(
        self,
        conversation_id: UUID,
    ) -> int:

        statement = delete(
            ChatMessage
        ).where(
            ChatMessage.conversation_id
            == conversation_id
        )

        result = await self.session.execute(
            statement
        )

        await self.session.flush()

        return result.rowcount or 0
    
    
    async def list_cursor_page(
        self,
        conversation_id: UUID,
        limit: int = 20,
        cursor: MessageCursor | None = None,
    ) -> tuple[list[ChatMessage], bool]:
        """
        Load the latest message page or messages older than a cursor.

        Database query order:
            newest -> oldest

        Returned API order:
            oldest -> newest

        One extra row is fetched to determine whether older messages
        still exist.
        """

        statement = select(
            ChatMessage
        ).where(
            ChatMessage.conversation_id
            == conversation_id
        )

        if cursor is not None:
            statement = statement.where(
                or_(
                    ChatMessage.created_at
                    < cursor.created_at,

                    and_(
                        ChatMessage.created_at
                        == cursor.created_at,

                        ChatMessage.id
                        < cursor.message_id,
                    ),
                )
            )

        statement = (
            statement
            .order_by(
                ChatMessage.created_at.desc(),
                ChatMessage.id.desc(),
            )
            .limit(limit + 1)
        )

        result = await self.session.execute(
            statement
        )

        messages = list(
            result.scalars().all()
        )

        has_more = len(messages) > limit

        if has_more:
            messages = messages[:limit]

        # Frontend renders messages chronologically.
        messages.reverse()

        return messages, has_more