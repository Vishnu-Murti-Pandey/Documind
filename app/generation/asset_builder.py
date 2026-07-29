from app.models.table_reference import TableReference
from app.retrieval.search_results import SearchResult


class AssetBuilder:

    def build_tables(
        self,
        results: list[SearchResult],
    ) -> list[TableReference]:

        tables: list[TableReference] = []

        seen_tables = set()

        for result in results:

            for table in result.tables:

                html = table.get("html")

                if not html:
                    continue

                if html in seen_tables:
                    continue

                tables.append(

                    TableReference(

                        chunk_id=result.chunk_id,

                        summary=table.get("summary"),

                        html=html,

                    )

                )

                seen_tables.add(html)

        return tables