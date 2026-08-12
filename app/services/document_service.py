"""
Document management service.
"""

import asyncio
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.document import (
    DocumentItem,
    DocumentListResponse,
)
from app.models.document import Document
from app.repositories.document_repository import (
    DocumentRepository,
)
from app.storage.minio_storage import MinioStorage


class DocumentNotFoundError(Exception):
    pass


class DuplicateDocumentError(Exception):
    pass


class DocumentService:

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:

        self.session = session

        self.repository = DocumentRepository(
            session
        )

        self.storage = MinioStorage()

    @staticmethod
    def to_response(
        document: Document,
    ) -> DocumentItem:

        return DocumentItem(
            id=document.id,
            paper_name=document.paper_name,
            original_filename=(
                document.original_filename
            ),
            status=document.status.value,
            file_size_bytes=document.file_size_bytes,
            elements_count=document.elements_count,
            chunks_count=document.chunks_count,
            error_message=document.error_message,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    async def list_documents(
        self,
        page: int,
        limit: int,
    ) -> DocumentListResponse:

        stale_count = await self.repository.fail_stale_processing()
        if stale_count:
            await self.session.commit()

        documents, total = (
            await self.repository.list_paginated(
                page=page,
                limit=limit,
            )
        )

        return DocumentListResponse(
            items=[
                self.to_response(document)
                for document in documents
            ],
            page=page,
            limit=limit,
            total=total,
            has_more=((page + 1) * limit < total),
        )

    async def get_document(
        self,
        paper_name: str,
    ) -> DocumentItem:

        document = (
            await self.repository.get_by_paper_name(
                paper_name
            )
        )

        if document is None:
            raise DocumentNotFoundError(
                paper_name
            )

        return self.to_response(
            document
        )

    async def prepare_ingestion(
        self,
        paper_name: str,
        original_filename: str,
        file_size_bytes: int,
        overwrite: bool,
    ) -> Document:

        existing = (
            await self.repository.get_by_paper_name(
                paper_name
            )
        )

        if existing is None:
            document = await self.repository.create(
                paper_name=paper_name,
                original_filename=original_filename,
                file_size_bytes=file_size_bytes,
            )

            await self.session.commit()
            await self.session.refresh(document)

            return document

        if not overwrite:
            raise DuplicateDocumentError(
                paper_name
            )

        # Remove previously indexed data before re-ingestion.
        await self.cleanup_document_data(
            paper_name
        )

        document = (
            await self.repository.reset_for_reingestion(
                document=existing,
                original_filename=original_filename,
                file_size_bytes=file_size_bytes,
            )
        )

        await self.session.commit()
        await self.session.refresh(document)

        return document

    async def mark_processing(
        self,
        document: Document,
    ) -> None:

        try:
            await self.repository.mark_processing(
                document
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

    async def mark_completed(
        self,
        document: Document,
        elements_count: int,
        chunks_count: int,
    ) -> None:

        try:
            await self.repository.mark_completed(
                document=document,
                elements_count=elements_count,
                chunks_count=chunks_count,
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

    async def mark_failed(
        self,
        document: Document,
        error_message: str,
    ) -> None:

        try:
            await self.repository.mark_failed(
                document=document,
                error_message=error_message,
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

    async def cleanup_document_data(
        self,
        paper_name: str,
    ) -> None:
        """
        Remove paper data from Qdrant and MinIO.

        Both clients are synchronous, so they run in threads.
        """

        # Listing documents does not need FastEmbed. Load vector support only
        # for destructive cleanup operations.
        from app.vectorstore.store import VectorStore

        vector_store = VectorStore()

        await asyncio.gather(
            asyncio.to_thread(
                vector_store.delete_by_paper_name,
                paper_name,
            ),
            asyncio.to_thread(
                self.storage.delete_paper_assets,
                paper_name,
            ),
        )

    async def delete_document(
        self,
        paper_name: str,
    ) -> None:

        document = (
            await self.repository.get_by_paper_name(
                paper_name
            )
        )

        if document is None:
            raise DocumentNotFoundError(
                paper_name
            )

        # First clean external data. Delete the DB row only after
        # external cleanup succeeds.
        await self.cleanup_document_data(
            paper_name
        )

        try:
            await self.repository.delete(
                document
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise
