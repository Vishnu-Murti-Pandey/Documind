from pydantic import BaseModel

from app.models.citation import Citation
from app.models.figure_reference import FigureReference
from app.models.table_reference import TableReference


class RAGResponse(BaseModel):
    answer: str
    citations: list[Citation]
    figures: list[FigureReference]
    tables: list[TableReference]