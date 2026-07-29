from typing import Any

from pydantic import BaseModel


class FigureReference(BaseModel):
    """
    Figure returned by the RAG pipeline.

    This model is used throughout:
    - FigureBuilder
    - FigureReranker
    - PromptBuilder
    - RAGResponse
    - Frontend/API
    """

    score: float = 0.0

    chunk_id: str

    paper_name: str

    section_title: str

    page_start: int

    page_end: int

    caption: str | None = None

    description: str | None = None

    storage: dict[str, Any]