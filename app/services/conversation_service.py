"""
Conversation management service.

Used by frontend-facing conversation APIs.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.conversation import (
    ChatMessageItem,
    ConversationDetailResponse,
    ConversationItem,
    ConversationListResponse,
    ConversationMessagesResponse,
)
from app.repositories.chat_message_repository import (
    ChatMessageRepository,
)
from app.repositories.conversation_repository import (
    ConversationRepository,
)


class ConversationNotFoundError(Exception):
    """
    Raised when a requested conversation does not exist.
    """


class ConversationService:

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.conversation_repository = (
            ConversationRepository(session)
        )

        self.message_repository = (
            ChatMessageRepository(session)
        )

    async def list_conversations(
        self,
        page: int,
        limit: int,
    ) -> ConversationListResponse:

        conversations, total = (
            await self.conversation_repository.list_paginated(
                page=page,
                limit=limit,
                active_only=True,
            )
        )

        items = [
            ConversationItem(
                conversation_id=conversation.public_id,
                title=conversation.title,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
            )
            for conversation in conversations
        ]

        return ConversationListResponse(
            items=items,
            page=page,
            limit=limit,
            total=total,
            has_more=((page + 1) * limit < total),
        )

    async def get_conversation(
        self,
        public_id: str,
    ) -> ConversationDetailResponse:

        conversation = (
            await self.conversation_repository.get_by_public_id(
                public_id=public_id,
                active_only=True,
            )
        )

        if conversation is None:
            raise ConversationNotFoundError(
                public_id
            )

        return ConversationDetailResponse(
            conversation_id=conversation.public_id,
            title=conversation.title,
            summary=conversation.summary,
            is_active=conversation.is_active,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    async def get_messages(
        self,
        public_id: str,
        page: int,
        limit: int,
    ) -> ConversationMessagesResponse:

        conversation = (
            await self.conversation_repository.get_by_public_id(
                public_id=public_id,
                active_only=True,
            )
        )

        if conversation is None:
            raise ConversationNotFoundError(
                public_id
            )

        messages, total = (
            await self.message_repository.list_paginated(
                conversation_id=conversation.id,
                page=page,
                limit=limit,
            )
        )

        message_items = [
            ChatMessageItem(
                id=message.id,
                role=message.role.value,
                content=message.content,
                citations=message.citations or [],
                figures=message.figures or [],
                tables=message.tables or [],
                created_at=message.created_at,
            )
            for message in messages
        ]

        return ConversationMessagesResponse(
            conversation_id=conversation.public_id,
            title=conversation.title,
            messages=message_items,
            page=page,
            limit=limit,
            total=total,
            has_more=((page + 1) * limit < total),
        )

    async def rename_conversation(
        self,
        public_id: str,
        title: str,
    ) -> ConversationDetailResponse:

        conversation = (
            await self.conversation_repository.get_by_public_id(
                public_id=public_id,
                active_only=True,
            )
        )

        if conversation is None:
            raise ConversationNotFoundError(
                public_id
            )

        try:
            conversation = (
                await self.conversation_repository.update_title(
                    conversation=conversation,
                    title=title,
                )
            )

            await self.session.commit()

            await self.session.refresh(
                conversation
            )

            return ConversationDetailResponse(
                conversation_id=conversation.public_id,
                title=conversation.title,
                summary=conversation.summary,
                is_active=conversation.is_active,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
            )

        except Exception:
            await self.session.rollback()
            raise

    async def delete_conversation(
        self,
        public_id: str,
    ) -> None:
        """
        Permanently delete a conversation and all messages.
        """

        conversation = (
            await self.conversation_repository.get_by_public_id(
                public_id=public_id,
            )
        )

        if conversation is None:
            raise ConversationNotFoundError(
                public_id
            )

        try:
            await self.conversation_repository.delete(
                conversation
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise