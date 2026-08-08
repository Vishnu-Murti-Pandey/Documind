"""
Schemas used by conversation management APIs.
"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationItem(BaseModel):
    """
    Conversation shown in the frontend sidebar.
    """

    conversation_id: str
    title: str | None
    paper_name: str | None

    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    """
    Paginated conversation list.
    """

    items: list[ConversationItem]

    page: int
    limit: int
    total: int
    has_more: bool


class ConversationDetailResponse(BaseModel):
    """
    Basic information about one conversation.
    """

    conversation_id: str
    title: str | None
    summary: str | None
    is_active: bool

    created_at: datetime
    updated_at: datetime


class ConversationUpdateRequest(BaseModel):
    """
    Fields that can currently be modified.
    """

    title: str = Field(
        min_length=1,
        max_length=255,
    )


class ChatMessageItem(BaseModel):
    """
    One persisted frontend chat message.
    """
    
    id: UUID

    role: Literal[
        "user",
        "assistant",
        "system",
    ]

    content: str

    citations: list[dict[str, Any]] = Field(
        default_factory=list
    )

    figures: list[dict[str, Any]] = Field(
        default_factory=list
    )

    tables: list[dict[str, Any]] = Field(
        default_factory=list
    )

    created_at: datetime


class ConversationMessagesResponse(BaseModel):
    conversation_id: str
    title: str | None
    paper_name: str | None

    messages: list[ChatMessageItem]

    next_cursor: str | None
    has_more: bool