"""
Document repository.
"""

from uuid import UUID

from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import (
    Document,
    DocumentStatus,
)


class DocumentRepository:

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def create(
        self,
        paper_name: str,
        original_filename: str,
        file_size_bytes: int,
    ) -> Document:

        document = Document(
            paper_name=paper_name,
            original_filename=original_filename,
            file_size_bytes=file_size_bytes,
            status=DocumentStatus.PENDING,
        )

        self.session.add(document)

        await self.session.flush()

        return document

    async def get_by_id(
        self,
        document_id: UUID,
    ) -> Document | None:

        return await self.session.get(
            Document,
            document_id,
        )

    async def get_by_paper_name(
        self,
        paper_name: str,
    ) -> Document | None:

        statement = select(
            Document
        ).where(
            Document.paper_name == paper_name
        )

        result = await self.session.execute(
            statement
        )

        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        page: int,
        limit: int,
    ) -> tuple[list[Document], int]:

        offset = page * limit

        count_result = await self.session.execute(
            select(
                func.count(Document.id)
            )
        )

        total = int(
            count_result.scalar_one()
        )

        statement = (
            select(Document)
            .order_by(
                Document.updated_at.desc(),
                Document.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(
            statement
        )

        return (
            list(result.scalars().all()),
            total,
        )

    async def mark_processing(
        self,
        document: Document,
    ) -> Document:

        document.status = DocumentStatus.PROCESSING
        document.error_message = None

        await self.session.flush()

        return document

    async def mark_completed(
        self,
        document: Document,
        elements_count: int,
        chunks_count: int,
    ) -> Document:

        document.status = DocumentStatus.COMPLETED
        document.elements_count = elements_count
        document.chunks_count = chunks_count
        document.error_message = None

        await self.session.flush()

        return document

    async def mark_failed(
        self,
        document: Document,
        error_message: str,
    ) -> Document:

        document.status = DocumentStatus.FAILED
        document.error_message = error_message[:5000]

        await self.session.flush()

        return document

    async def reset_for_reingestion(
        self,
        document: Document,
        original_filename: str,
        file_size_bytes: int,
    ) -> Document:

        document.original_filename = original_filename
        document.file_size_bytes = file_size_bytes
        document.status = DocumentStatus.PENDING

        document.elements_count = None
        document.chunks_count = None
        document.error_message = None

        await self.session.flush()

        return document

    async def delete(
        self,
        document: Document,
    ) -> None:

        await self.session.delete(
            document
        )

        await self.session.flush()