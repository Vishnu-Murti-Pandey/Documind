"""
Asynchronous streaming ingestion pipeline.

Pipeline
--------
PDF
    ↓
Parse
    ↓
Chunk
    ↓
Image Enrichment
    ↓
Table Enrichment
    ↓
Embedding
    ↓
Qdrant

The underlying ingestion components are synchronous, so blocking
operations are executed with asyncio.to_thread() to avoid blocking
FastAPI's event loop.
"""

import asyncio
import logging
import time
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from app.chunking.chunker import DocumentChunker
from app.embedding.embedding_builder import EmbeddingBuilder
from app.embedding.embedding_generator import EmbeddingGenerator
from app.enrichment.image_enricher import ImageEnricher
from app.enrichment.table_enricher import TableEnricher
from app.parser.pdf_parser import PDFParser
from app.vectorstore.collection import CollectionManager
from app.vectorstore.store import VectorStore


logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Ingest one PDF while emitting structured progress events.
    """

    def __init__(self) -> None:
        self.chunker = DocumentChunker()

        self.image_enricher = ImageEnricher()
        self.table_enricher = TableEnricher()

        self.embedding_builder = EmbeddingBuilder()
        self.embedding_generator = EmbeddingGenerator()

        self.collection_manager = CollectionManager()
        self.vector_store = VectorStore()

    async def stream(
        self,
        pdf_path: str | Path,
        paper_name: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Stream ingestion progress.

        Event structure:

        {
            "type": "status",
            "data": {
                "stage": "parsing",
                "message": "Parsing PDF...",
                "progress": 10
            }
        }
        """

        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(
                f"PDF file not found: {pdf_path}"
            )

        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError(
                "Only PDF files are supported."
            )

        resolved_paper_name = (
            paper_name.strip()
            if paper_name
            else pdf_path.stem
        )

        if not resolved_paper_name:
            raise ValueError(
                "Paper name cannot be empty."
            )

        started_at = time.perf_counter()

        try:
            # ==================================================
            # Started
            # ==================================================

            yield {
                "type": "started",
                "data": {
                    "paper_name": resolved_paper_name,
                    "message": "Ingestion started.",
                    "progress": 0,
                },
            }

            # ==================================================
            # Parse PDF
            # ==================================================

            yield {
                "type": "status",
                "data": {
                    "stage": "parsing",
                    "message": "Parsing PDF contents...",
                    "progress": 5,
                },
            }

            parser = PDFParser(
                pdf_path
            )

            elements = await asyncio.to_thread(
                parser.parse_to_json
            )

            yield {
                "type": "status",
                "data": {
                    "stage": "parsed",
                    "message": (
                        f"Parsed {len(elements)} document elements."
                    ),
                    "elements_count": len(elements),
                    "progress": 15,
                },
            }

            # ==================================================
            # Chunk document
            # ==================================================

            yield {
                "type": "status",
                "data": {
                    "stage": "chunking",
                    "message": "Creating document chunks...",
                    "progress": 18,
                },
            }

            chunks = await asyncio.to_thread(
                self.chunker.create_chunks,
                elements,
                resolved_paper_name,
            )

            total_chunks = len(
                chunks
            )

            if total_chunks == 0:
                raise RuntimeError(
                    "No chunks were created from the PDF."
                )

            yield {
                "type": "status",
                "data": {
                    "stage": "chunked",
                    "message": (
                        f"Created {total_chunks} chunks."
                    ),
                    "total_chunks": total_chunks,
                    "progress": 25,
                },
            }

            # ==================================================
            # Ensure Qdrant collection
            # ==================================================

            yield {
                "type": "status",
                "data": {
                    "stage": "collection",
                    "message": (
                        "Preparing the vector collection..."
                    ),
                    "progress": 27,
                },
            }

            await asyncio.to_thread(
                self.collection_manager.create
            )

            # ==================================================
            # Process chunks
            # ==================================================

            # Chunk processing occupies progress 30 through 95.
            chunk_progress_start = 30.0
            chunk_progress_range = 65.0
            progress_per_chunk = (
                chunk_progress_range / total_chunks
            )

            for index, chunk in enumerate(
                chunks,
                start=1,
            ):
                chunk_id = chunk.get(
                    "chunk_id",
                    f"chunk-{index}",
                )

                chunk_start_progress = (
                    chunk_progress_start
                    + (index - 1) * progress_per_chunk
                )

                yield {
                    "type": "chunk_progress",
                    "data": {
                        "stage": "processing_chunk",
                        "message": (
                            f"Processing chunk "
                            f"{index} of {total_chunks}."
                        ),
                        "chunk_id": chunk_id,
                        "current_chunk": index,
                        "total_chunks": total_chunks,
                        "progress": round(
                            chunk_start_progress,
                            2,
                        ),
                    },
                }

                # ----------------------------------------------
                # Image enrichment
                # ----------------------------------------------

                yield {
                    "type": "status",
                    "data": {
                        "stage": "image_enrichment",
                        "message": (
                            f"Analyzing images in "
                            f"chunk {index}/{total_chunks}..."
                        ),
                        "chunk_id": chunk_id,
                        "current_chunk": index,
                        "total_chunks": total_chunks,
                        "progress": round(
                            chunk_start_progress
                            + progress_per_chunk * 0.20,
                            2,
                        ),
                    },
                }

                chunk = await asyncio.to_thread(
                    self.image_enricher.enrich_chunk,
                    chunk,
                )

                # ----------------------------------------------
                # Table enrichment
                # ----------------------------------------------

                yield {
                    "type": "status",
                    "data": {
                        "stage": "table_enrichment",
                        "message": (
                            f"Analyzing tables in "
                            f"chunk {index}/{total_chunks}..."
                        ),
                        "chunk_id": chunk_id,
                        "current_chunk": index,
                        "total_chunks": total_chunks,
                        "progress": round(
                            chunk_start_progress
                            + progress_per_chunk * 0.40,
                            2,
                        ),
                    },
                }

                chunk = await asyncio.to_thread(
                    self.table_enricher.enrich_chunk,
                    chunk,
                )

                # ----------------------------------------------
                # Build embedding document
                # ----------------------------------------------

                yield {
                    "type": "status",
                    "data": {
                        "stage": "embedding",
                        "message": (
                            f"Generating embeddings for "
                            f"chunk {index}/{total_chunks}..."
                        ),
                        "chunk_id": chunk_id,
                        "current_chunk": index,
                        "total_chunks": total_chunks,
                        "progress": round(
                            chunk_start_progress
                            + progress_per_chunk * 0.60,
                            2,
                        ),
                    },
                }

                embedding_document = await asyncio.to_thread(
                    self.embedding_builder.build_document,
                    chunk,
                )

                vector_document = await asyncio.to_thread(
                    self.embedding_generator.generate,
                    embedding_document,
                )

                # ----------------------------------------------
                # Store in Qdrant
                # ----------------------------------------------

                yield {
                    "type": "status",
                    "data": {
                        "stage": "storing",
                        "message": (
                            f"Storing chunk "
                            f"{index}/{total_chunks} in Qdrant..."
                        ),
                        "chunk_id": chunk_id,
                        "current_chunk": index,
                        "total_chunks": total_chunks,
                        "progress": round(
                            chunk_start_progress
                            + progress_per_chunk * 0.85,
                            2,
                        ),
                    },
                }

                await asyncio.to_thread(
                    self.vector_store.insert,
                    vector_document,
                )

                completed_progress = (
                    chunk_progress_start
                    + index * progress_per_chunk
                )

                yield {
                    "type": "chunk_progress",
                    "data": {
                        "stage": "chunk_completed",
                        "message": (
                            f"Chunk {index}/{total_chunks} "
                            f"stored successfully."
                        ),
                        "chunk_id": chunk_id,
                        "current_chunk": index,
                        "total_chunks": total_chunks,
                        "progress": round(
                            completed_progress,
                            2,
                        ),
                    },
                }

            # ==================================================
            # Completed
            # ==================================================

            elapsed_seconds = (
                time.perf_counter()
                - started_at
            )

            yield {
                "type": "completed",
                "data": {
                    "status": "completed",
                    "paper_name": resolved_paper_name,
                    "elements_count": len(elements),
                    "chunks_stored": total_chunks,
                    "elapsed_seconds": round(
                        elapsed_seconds,
                        2,
                    ),
                    "message": (
                        "Document ingestion completed successfully."
                    ),
                    "progress": 100,
                },
            }

        except asyncio.CancelledError:
            logger.info(
                "Ingestion stream was cancelled for paper %s.",
                resolved_paper_name,
            )

            raise

        except Exception as exc:
            logger.exception(
                "Ingestion failed for paper %s.",
                resolved_paper_name,
            )

            yield {
                "type": "error",
                "data": {
                    "status": "failed",
                    "paper_name": resolved_paper_name,
                    "message": "Document ingestion failed.",
                    # Useful during development. Remove or hide this
                    # field in production if errors may contain
                    # sensitive details.
                    "detail": str(exc),
                },
            }