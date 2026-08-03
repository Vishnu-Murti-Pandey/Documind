"""
Conversation repository.

Contains all database operations related to conversations.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.conversation import Conversation


class ConversationRepository:
    """
    Repository for Conversation database operations.

    Transaction commits are controlled by the service layer.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def create(
        self,
        public_id: str,
        title: str | None = None,
    ) -> Conversation:

        conversation = Conversation(
            public_id=public_id,
            title=title,
        )

        self.session.add(conversation)

        await self.session.flush()

        return conversation

    async def get_by_id(
        self,
        conversation_id: UUID,
    ) -> Conversation | None:

        return await self.session.get(
            Conversation,
            conversation_id,
        )

    async def get_by_public_id(
        self,
        public_id: str,
        active_only: bool = False,
    ) -> Conversation | None:

        statement = select(
            Conversation
        ).where(
            Conversation.public_id == public_id
        )

        if active_only:
            statement = statement.where(
                Conversation.is_active.is_(True)
            )

        result = await self.session.execute(
            statement
        )

        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        public_id: str,
        title: str | None = None,
    ) -> tuple[Conversation, bool]:

        conversation = await self.get_by_public_id(
            public_id
        )

        if conversation is not None:
            return conversation, False

        conversation = await self.create(
            public_id=public_id,
            title=title,
        )

        return conversation, True

    async def list_paginated(
        self,
        page: int = 0,
        limit: int = 20,
        active_only: bool = True,
    ) -> tuple[list[Conversation], int]:
        """
        Return paginated conversations and the total count.

        Conversations are ordered by latest activity.
        """

        offset = page * limit

        filters = []

        if active_only:
            filters.append(
                Conversation.is_active.is_(True)
            )

        count_statement = select(
            func.count(Conversation.id)
        )

        if filters:
            count_statement = count_statement.where(
                *filters
            )

        count_result = await self.session.execute(
            count_statement
        )

        total = int(
            count_result.scalar_one()
        )

        statement = (
            select(Conversation)
            .where(*filters)
            .order_by(
                Conversation.updated_at.desc(),
                Conversation.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(
            statement
        )

        conversations = list(
            result.scalars().all()
        )

        return conversations, total

    async def update_title(
        self,
        conversation: Conversation,
        title: str,
    ) -> Conversation:

        title = title.strip()

        if not title:
            raise ValueError(
                "Conversation title cannot be empty."
            )

        conversation.title = title

        await self.touch(
            conversation
        )

        await self.session.flush()

        return conversation

    async def update_summary(
        self,
        conversation: Conversation,
        summary: str | None,
    ) -> Conversation:

        conversation.summary = (
            summary.strip()
            if summary
            else None
        )

        await self.touch(
            conversation
        )

        await self.session.flush()

        return conversation

    async def touch(
        self,
        conversation: Conversation,
    ) -> Conversation:

        conversation.updated_at = datetime.now(
            timezone.utc
        )

        await self.session.flush()

        return conversation

    async def deactivate(
        self,
        conversation: Conversation,
    ) -> Conversation:
        """
        Soft-delete a conversation.
        """

        conversation.is_active = False

        await self.touch(
            conversation
        )

        return conversation

    async def activate(
        self,
        conversation: Conversation,
    ) -> Conversation:

        conversation.is_active = True

        await self.touch(
            conversation
        )

        return conversation

    async def delete(
        self,
        conversation: Conversation,
    ) -> None:
        """
        Permanently delete the conversation and its messages.
        """

        await self.session.delete(
            conversation
        )

        await self.session.flush()