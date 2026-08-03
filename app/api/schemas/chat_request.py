from pydantic import BaseModel, Field

from app.models.search_filter import SearchFilter


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=10_000,
    )

    conversation_id: str | None = Field(
        default=None,
        max_length=100,
    )

    filter: SearchFilter | None = None