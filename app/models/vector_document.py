from typing import Any
from pydantic import BaseModel


class VectorDocument(BaseModel):
    chunk_id: str
    paper_name: str
    section_title: str
    embedding: list[float]
    chunk_text: str
    images: list[dict[str, Any]]
    tables: list[dict[str, Any]]
    metadata: dict[str, Any]