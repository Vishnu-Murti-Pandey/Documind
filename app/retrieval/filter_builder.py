from qdrant_client.models import (
    FieldCondition,
    Filter,
    MatchValue,
    Range,
)

from app.models.search_filter import SearchFilter


class FilterBuilder:
    def build(
        self,
        search_filter: SearchFilter | None,
    ) -> Filter | None:

        if search_filter is None:
            return None

        must = []

        # ----------------------------------------------------
        # Paper
        # ----------------------------------------------------

        if search_filter.paper_name:

            must.append(
                FieldCondition(
                    key="paper_name",
                    match=MatchValue(
                        value=search_filter.paper_name,
                    ),
                )
            )

        # ----------------------------------------------------
        # Section
        # ----------------------------------------------------

        if search_filter.section_title:

            must.append(
                FieldCondition(
                    key="section_title",
                    match=MatchValue(
                        value=search_filter.section_title,
                    ),
                )
            )

        # ----------------------------------------------------
        # Page overlap
        # ----------------------------------------------------

        if (
            search_filter.page_start is not None
            and
            search_filter.page_end is not None
        ):

            # chunk.page_start <= requested.page_end

            must.append(
                FieldCondition(
                    key="page_start",
                    range=Range(
                        lte=search_filter.page_end,
                    ),
                )
            )

            # chunk.page_end >= requested.page_start

            must.append(
                FieldCondition(
                    key="page_end",
                    range=Range(
                        gte=search_filter.page_start,
                    ),
                )
            )

        elif search_filter.page_start is not None:
            must.append(
                FieldCondition(
                    key="page_end",
                    range=Range(
                        gte=search_filter.page_start,
                    ),
                )
            )

        elif search_filter.page_end is not None:
            must.append(
                FieldCondition(
                    key="page_start",
                    range=Range(
                        lte=search_filter.page_end,
                    ),
                )
            )

        if not must:
            return None

        return Filter(
            must=must,
        )