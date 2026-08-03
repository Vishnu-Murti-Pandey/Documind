from pydantic import BaseModel


class TableReference(BaseModel):
    """
    Table returned by the RAG pipeline.
    """

    chunk_id: str

    paper_name: str

    section_title: str

    page_start: int

    page_end: int

    summary: str | None = None

    html: str