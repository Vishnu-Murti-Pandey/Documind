"""
Build frontend-ready figure references.

The frontend receives stable FastAPI URLs.
MinIO details remain internal to the backend.
"""

from urllib.parse import quote

from app.models.figure_reference import FigureReference
from app.retrieval.search_results import SearchResult


class FigureBuilder:

    def build(
        self,
        results: list[SearchResult],
    ) -> list[FigureReference]:

        figures: list[FigureReference] = []

        seen: set[str] = set()

        for result in results:

            for image in result.images:

                storage = image.get("storage")

                if not storage:
                    continue

                object_name = storage.get(
                    "object_name"
                )

                if not object_name:
                    continue

                if object_name in seen:
                    continue

                # Preserve path separators while safely encoding
                # spaces and other URL-sensitive characters.
                encoded_object_name = quote(
                    object_name,
                    safe="/",
                )

                figures.append(
                    FigureReference(
                        score=result.score,
                        chunk_id=result.chunk_id,
                        paper_name=result.paper_name,
                        section_title=result.section_title,
                        page_start=result.page_start,
                        page_end=result.page_end,
                        caption=image.get("caption"),
                        description=image.get(
                            "description"
                        ),
                        image_url=(
                            f"/api/assets/"
                            f"{encoded_object_name}"
                        ),
                    )
                )

                seen.add(object_name)

        return figures