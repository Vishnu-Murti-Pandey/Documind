from pydantic import BaseModel


class TableReference(BaseModel):
    chunk_id: str
    summary: str | None = None
    html: str