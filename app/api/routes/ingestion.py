"""
Streaming document-ingestion API.
"""

import asyncio
import logging
import re
import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse

from app.api.sse import sse_event
from app.ingest import IngestionPipeline


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/ingestion",
    tags=["Ingestion"],
)


def sanitize_paper_name(
    filename: str,
) -> str:
    """
    Convert an uploaded filename into a safe paper identifier.
    """

    name = Path(
        filename
    ).stem.strip()

    name = re.sub(
        r"[^A-Za-z0-9._-]+",
        "-",
        name,
    )

    name = name.strip(
        "-_."
    )

    return name or "research-paper"


async def save_upload_to_temp(
    upload: UploadFile,
) -> Path:
    """
    Save the uploaded PDF to a temporary path.

    NamedTemporaryFile(delete=False) is used because Windows does
    not allow every library to reopen a file that is still open.
    """

    suffix = Path(
        upload.filename or "document.pdf"
    ).suffix.lower()

    with tempfile.NamedTemporaryFile(
        mode="wb",
        suffix=suffix,
        prefix="rag-ingestion-",
        delete=False,
    ) as temporary_file:
        temporary_path = Path(
            temporary_file.name
        )

        while True:
            data = await upload.read(
                1024 * 1024
            )

            if not data:
                break

            await asyncio.to_thread(
                temporary_file.write,
                data,
            )

    await upload.close()

    return temporary_path


@router.post("/stream")
async def stream_ingestion(
    file: UploadFile = File(...),
) -> StreamingResponse:
    """
    Upload and ingest one PDF while streaming progress using SSE.

    Event types:
    - upload
    - started
    - status
    - chunk_progress
    - completed
    - error
    """

    filename = file.filename or ""

    if not filename.lower().endswith(
        ".pdf"
    ):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are supported.",
        )

    if file.content_type not in {
        "application/pdf",
        "application/octet-stream",
        None,
    }:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Invalid PDF content type.",
        )

    temporary_path = await save_upload_to_temp(
        file
    )

    paper_name = sanitize_paper_name(
        filename
    )

    pipeline = IngestionPipeline()

    async def event_generator(
    ) -> AsyncGenerator[str, None]:
        try:
            yield sse_event(
                "upload",
                {
                    "status": "completed",
                    "filename": filename,
                    "paper_name": paper_name,
                    "message": "PDF uploaded successfully.",
                    "progress": 0,
                },
            )

            async for event in pipeline.stream(
                pdf_path=temporary_path,
                paper_name=paper_name,
            ):
                yield sse_event(
                    event["type"],
                    event["data"],
                )

        except asyncio.CancelledError:
            logger.info(
                "Ingestion client disconnected for %s.",
                paper_name,
            )

            raise

        except Exception as exc:
            logger.exception(
                "Ingestion route failed for %s.",
                paper_name,
            )

            yield sse_event(
                "error",
                {
                    "status": "failed",
                    "paper_name": paper_name,
                    "message": "Document ingestion failed.",
                    "detail": str(exc),
                },
            )

        finally:
            try:
                temporary_path.unlink(
                    missing_ok=True
                )
            except OSError:
                logger.warning(
                    "Could not remove temporary file: %s",
                    temporary_path,
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