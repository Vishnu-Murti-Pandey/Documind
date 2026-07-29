from app.retrieval.search_results import SearchResult


class ContextBuilder:

    def build(
        self,
        results: list[SearchResult],
    ) -> str:

        sections = []

        for index, result in enumerate(results, start=1):

            block = [

                f"Source {index}",

                f"Paper: {result.paper_name}",

                f"Section: {result.section_title}",

                f"Pages: {result.page_start}-{result.page_end}",

                "",

                "Content:",

                result.chunk_text,
            ]

            if result.images:

                block.append("")
                block.append("Figures")

                for i, image in enumerate(result.images, start=1):

                    block.append(f"\nFigure {i}")

                    if image.get("caption"):
                        block.append(
                            f"Caption: {image['caption']}"
                        )

                    if image.get("description"):
                        block.append(
                            f"Description: {image['description']}"
                        )

                    if image.get("object_name"):
                        block.append(
                            f"Object: {image['object_name']}"
                        )

            if result.tables:

                block.append("")
                block.append(
                    f"Tables: {len(result.tables)}"
                )

                for table in result.tables:

                    if table.get("summary"):

                        block.append(
                            table["summary"]
                        )

            sections.append(
                "\n".join(block)
            )

        return "\n\n" + "=" * 80 + "\n\n".join(sections)