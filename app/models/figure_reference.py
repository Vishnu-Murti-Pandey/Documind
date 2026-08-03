from pydantic import BaseModel


class FigureReference(BaseModel):
    """
    Renderable figure returned to the frontend.
    """

    score: float = 0.0

    chunk_id: str

    paper_name: str

    section_title: str

    page_start: int

    page_end: int

    caption: str | None = None

    description: str | None = None

    # Stable FastAPI URL, not an expiring MinIO URL.
    image_url: str