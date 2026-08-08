from pydantic import BaseModel

from app.models.citation import Citation
from app.models.figure_reference import FigureReference
from app.models.table_reference import TableReference


class ChatResponse(BaseModel):
    conversation_id: str
    paper_name: str | None

    answer: str
    citations: list[Citation]
    figures: list[FigureReference]
    tables: list[TableReference]