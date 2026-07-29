"""
Pydantic model representing a document that will be embedded
and stored in the vector database.
"""

from typing import Any
from pydantic import BaseModel


class EmbeddingDocument(BaseModel):
    """
    Represents one document ready for embedding.
    """

    chunk_id: str

    embedding_text: str

    paper_name: str

    section_title: str

    # Original chunk text
    chunk_text: str

    # Original multimodal assets
    images: list[dict[str, Any]]

    tables: list[dict[str, Any]]

    # Metadata
    metadata: dict[str, Any]