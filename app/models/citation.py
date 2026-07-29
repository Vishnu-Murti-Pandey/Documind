from typing import Any
from pydantic import BaseModel


class Citation(BaseModel):
    type: str
    chunk_id: str
    paper_name: str
    section_title: str
    page_start: int
    page_end: int
    caption: str | None = None
    storage: dict[str, Any] | None = None