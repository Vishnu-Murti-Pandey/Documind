"""
Citation returned with a RAG response.

Citations represent textual paper sources.
Renderable figures are returned separately through FigureReference.
"""

from typing import Literal

from pydantic import BaseModel


class Citation(BaseModel):

    type: Literal["section"] = "section"

    chunk_id: str

    paper_name: str

    section_title: str

    page_start: int

    page_end: int

    caption: str | None = None