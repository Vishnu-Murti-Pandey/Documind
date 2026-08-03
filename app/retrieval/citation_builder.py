"""
Build textual citations from retrieved chunks.

Figures are not added here because they are returned separately
as FigureReference objects.
"""

from app.models.citation import Citation
from app.retrieval.search_results import SearchResult


class CitationBuilder:

    def build(
        self,
        results: list[SearchResult],
    ) -> list[Citation]:

        citations: list[Citation] = []

        seen_sections: set[
            tuple[str, str]
        ] = set()

        for result in results:

            section_key = (
                result.chunk_id,
                result.section_title,
            )

            if section_key in seen_sections:
                continue

            citations.append(
                Citation(
                    type="section",
                    chunk_id=result.chunk_id,
                    paper_name=result.paper_name,
                    section_title=result.section_title,
                    page_start=result.page_start,
                    page_end=result.page_end,
                )
            )

            seen_sections.add(section_key)

        return citations