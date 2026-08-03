"""
Schemas for document-management APIs.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


DocumentStatusValue = Literal[
    "pending",
    "processing",
    "completed",
    "failed",
]


class DocumentItem(BaseModel):
    id: UUID
    paper_name: str
    original_filename: str
    status: DocumentStatusValue

    file_size_bytes: int

    elements_count: int | None
    chunks_count: int | None

    error_message: str | None

    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentItem]

    page: int
    limit: int
    total: int
    has_more: bool