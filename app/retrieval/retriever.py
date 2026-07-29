"""
Hybrid Retriever (Dense + Sparse + Metadata Filters)
"""

from qdrant_client.models import (
    Fusion,
    FusionQuery,
    Prefetch,
    SparseVector,
)

from app.models.query import QueryEmbedding
from app.retrieval.filter_builder import FilterBuilder
from app.models.search_filter import SearchFilter
from app.retrieval.search_results import SearchResult
from app.vectorstore.client import VectorClient
from app.vectorstore.collection import COLLECTION_NAME


class Retriever:

    def __init__(self):

        self.client = VectorClient().client
        self.filter_builder = FilterBuilder()

    def retrieve(
        self,
        query: QueryEmbedding,
        top_k: int = 10,
        search_filter: SearchFilter | None = None,
    ) -> list[SearchResult]:

        qdrant_filter = self.filter_builder.build(search_filter)

        response = self.client.query_points(

            collection_name=COLLECTION_NAME,

            prefetch=[

                Prefetch(
                    query=query.dense,
                    using="dense",
                    limit=30,
                ),

                Prefetch(
                    query=SparseVector(
                        indices=query.sparse_indices,
                        values=query.sparse_values,
                    ),
                    using="sparse",
                    limit=30,
                ),

            ],

            query=FusionQuery(
                fusion=Fusion.RRF,
            ),

            query_filter=qdrant_filter,

            limit=top_k,

            with_payload=True,
        )

        results: list[SearchResult] = []

        for point in response.points:

            payload = point.payload

            results.append(

                SearchResult(

                    score=point.score,

                    chunk_id=payload["chunk_id"],

                    paper_name=payload["paper_name"],

                    section_title=payload["section_title"],

                    chunk_text=payload["chunk_text"],

                    page_start=payload["page_start"],

                    page_end=payload["page_end"],

                    token_count=payload["token_count"],

                    images=payload["images"],

                    tables=payload["tables"],

                    metadata=payload,

                )

            )

        return results