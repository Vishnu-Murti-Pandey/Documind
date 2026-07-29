from typing import Any
from pydantic import BaseModel


class SearchResult(BaseModel):
    score: float
    chunk_id: str
    paper_name: str
    section_title: str
    chunk_text: str
    page_start: int
    page_end: int
    token_count: int
    images: list[dict[str, Any]]
    tables: list[dict[str, Any]]
    metadata: dict[str, Any]