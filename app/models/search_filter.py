from pydantic import BaseModel


class SearchFilter(BaseModel):
    paper_name: str | None = None
    section_title: str | None = None
    page_start: int | None = None
    page_end: int | None = None