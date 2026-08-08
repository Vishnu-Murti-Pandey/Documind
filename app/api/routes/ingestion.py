"""
Streaming ingestion route with:

- upload-size protection
- PDF signature validation
- duplicate protection
- overwrite support
- PostgreSQL status tracking
- failed-ingestion cleanup
"""

import asyncio
import logging
import re
import tempfile
import threading
from collections.abc import AsyncGenerator
from pathlib import Path
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.sse import sse_event
from app.config import (
    MAX_UPLOAD_SIZE_BYTES,
    MAX_UPLOAD_SIZE_MB,
)
from app.db.session import get_db_session
from app.ingest import IngestionPipeline, IngestionCancelledError
from app.repositories.document_repository import DocumentRepository
from app.services.document_service import (
    DocumentService,
    DuplicateDocumentError,
)


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/ingestion",
    tags=["Ingestion"],
)

# Active jobs live in this process. The thread-safe event can be observed by
# the async pipeline between blocking parsing/enrichment/embedding stages.
_active_ingestions: dict[UUID, threading.Event] = {}


@router.post("/{document_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
async def cancel_ingestion(
    document_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    cancel_event = _active_ingestions.get(document_id)
    if cancel_event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active ingestion was found for this document.",
        )
    cancel_event.set()

    repository = DocumentRepository(session)
    document = await repository.get_by_id(document_id)
    if document is not None:
        await repository.mark_failed(
            document,
            "Document ingestion was cancelled.",
        )
        await session.commit()

    return {"status": "cancelling"}


def sanitize_paper_name(
    filename: str,
) -> str:

    name = Path(filename).stem.strip()

    name = re.sub(
        r"[^A-Za-z0-9._-]+",
        "-",
        name,
    )

    name = name.strip(
        "-_."
    )

    return name or "research-paper"


async def save_and_validate_pdf(
    upload: UploadFile,
) -> tuple[Path, int]:
    """
    Save an uploaded PDF while enforcing the size limit.

    Validation includes:
    - .pdf extension
    - PDF content type
    - %PDF file signature
    - maximum upload size
    """

    filename = upload.filename or ""

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            ),
            detail="Only PDF files are supported.",
        )

    if upload.content_type not in {
        "application/pdf",
        "application/octet-stream",
        None,
    }:
        raise HTTPException(
            status_code=(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            ),
            detail="Invalid PDF content type.",
        )

    temporary_path: Path | None = None
    total_size = 0
    first_bytes = b""

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=".pdf",
            prefix="rag-ingestion-",
            delete=False,
        ) as temporary_file:

            temporary_path = Path(
                temporary_file.name
            )

            while True:
                chunk = await upload.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                if not first_bytes:
                    first_bytes = chunk[:8]

                total_size += len(chunk)

                if total_size > MAX_UPLOAD_SIZE_BYTES:
                    raise HTTPException(
                        status_code=(
                            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
                        ),
                        detail=(
                            f"PDF exceeds the "
                            f"{MAX_UPLOAD_SIZE_MB} MB limit."
                        ),
                    )

                temporary_file.write(
                    chunk
                )

        if total_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded PDF is empty.",
            )

        if not first_bytes.startswith(
            b"%PDF-"
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
                ),
                detail=(
                    "The uploaded file is not a valid PDF."
                ),
            )

        return (
            temporary_path,
            total_size,
        )

    except Exception:
        if temporary_path:
            temporary_path.unlink(
                missing_ok=True
            )

        raise

    finally:
        await upload.close()


@router.post("/stream")
async def stream_ingestion(
    file: UploadFile = File(...),
    overwrite: bool = Query(
        default=False,
    ),
    session: AsyncSession = Depends(
        get_db_session
    ),
) -> StreamingResponse:

    filename = file.filename or "document.pdf"

    temporary_path, file_size_bytes = (
        await save_and_validate_pdf(file)
    )

    paper_name = sanitize_paper_name(
        filename
    )

    document_service = DocumentService(
        session
    )

    try:
        document = (
            await document_service.prepare_ingestion(
                paper_name=paper_name,
                original_filename=filename,
                file_size_bytes=file_size_bytes,
                overwrite=overwrite,
            )
        )

    except DuplicateDocumentError as exc:
        temporary_path.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This document already exists. "
                "Use overwrite=true to ingest it again."
            ),
        ) from exc

    cancel_event = threading.Event()
    pipeline = IngestionPipeline(cancel_event=cancel_event)
    _active_ingestions[document.id] = cancel_event

    async def event_generator(
    ) -> AsyncGenerator[str, None]:

        completed = False

        try:
            await document_service.mark_processing(
                document
            )

            yield sse_event(
                "document",
                {
                    "document_id": str(document.id),
                    "paper_name": paper_name,
                    "status": "processing",
                    "overwrite": overwrite,
                },
            )

            async for event in pipeline.stream(
                pdf_path=temporary_path,
                paper_name=paper_name,
            ):
                event_type = event["type"]
                event_data = event["data"]

                if event_type == "completed":
                    await document_service.mark_completed(
                        document=document,
                        elements_count=event_data.get(
                            "elements_count",
                            0,
                        ),
                        chunks_count=event_data.get(
                            "chunks_stored",
                            0,
                        ),
                    )

                    completed = True

                    event_data["document_id"] = str(
                        document.id
                    )

                elif event_type == "error":
                    error_message = event_data.get(
                        "detail",
                        event_data.get(
                            "message",
                            "Unknown ingestion failure.",
                        ),
                    )

                    # Clean partially written Qdrant/MinIO data.
                    try:
                        await document_service.cleanup_document_data(
                            paper_name
                        )
                    except Exception:
                        logger.exception(
                            "Failed to clean partial ingestion data."
                        )

                    await document_service.mark_failed(
                        document=document,
                        error_message=error_message,
                    )

                yield sse_event(
                    event_type,
                    event_data,
                )

        except (asyncio.CancelledError, IngestionCancelledError) as exc:
            logger.warning(
                "Ingestion cancelled for %s.",
                paper_name,
            )

            if not completed:
                try:
                    await document_service.cleanup_document_data(
                        paper_name
                    )
                    await document_service.mark_failed(
                        document=document,
                        error_message=(
                            "Document ingestion was cancelled."
                        ),
                    )
                except Exception:
                    logger.exception(
                        "Failed to mark ingestion as failed."
                    )

            if isinstance(exc, asyncio.CancelledError):
                raise

            return

        except Exception as exc:
            logger.exception(
                "Ingestion failed for %s.",
                paper_name,
            )

            try:
                await document_service.cleanup_document_data(
                    paper_name
                )
            except Exception:
                logger.exception(
                    "Failed to clean partial document data."
                )

            try:
                await document_service.mark_failed(
                    document=document,
                    error_message=str(exc),
                )
            except Exception:
                logger.exception(
                    "Failed to persist ingestion failure."
                )

            yield sse_event(
                "error",
                {
                    "document_id": str(document.id),
                    "paper_name": paper_name,
                    "status": "failed",
                    "message": "Document ingestion failed.",
                    "detail": str(exc),
                },
            )

        finally:
            _active_ingestions.pop(document.id, None)
            temporary_path.unlink(
                missing_ok=True
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
