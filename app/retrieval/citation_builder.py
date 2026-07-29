from app.models.citation import Citation
from app.retrieval.search_results import SearchResult


class CitationBuilder:

    def build(
        self,
        results: list[SearchResult],
    ) -> list[Citation]:

        citations: list[Citation] = []

        seen_sections = set()

        for result in results:

            section_key = (
                result.chunk_id,
                result.section_title,
            )

            if section_key not in seen_sections:

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

            for image in result.images:

                if not image.get("caption"):
                    continue

                citations.append(
                    Citation(
                        type="figure",
                        chunk_id=result.chunk_id,
                        paper_name=result.paper_name,
                        section_title=result.section_title,
                        page_start=result.page_start,
                        page_end=result.page_end,
                        caption=image.get("caption"),
                        storage=image.get("storage"),
                    )
                )

        return citations