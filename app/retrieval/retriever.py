"""
Hybrid Retriever.

Combines:
1. Dense vector retrieval.
2. Sparse BM25-style retrieval.
3. Reciprocal Rank Fusion.
4. Metadata filtering.
"""

import asyncio

from qdrant_client.models import (
    Fusion,
    FusionQuery,
    Prefetch,
    SparseVector,
)

from app.models.query import QueryEmbedding
from app.models.search_filter import SearchFilter
from app.retrieval.filter_builder import FilterBuilder
from app.retrieval.search_results import SearchResult
from app.vectorstore.client import VectorClient
from app.vectorstore.collection import COLLECTION_NAME


class Retriever:
    def __init__(self) -> None:
        self.client = VectorClient().client
        self.filter_builder = FilterBuilder()

    def retrieve(
        self,
        query: QueryEmbedding,
        top_k: int = 10,
        search_filter: SearchFilter | None = None,
    ) -> list[SearchResult]:
        """
        Synchronous Qdrant hybrid retrieval.
        """

        qdrant_filter = self.filter_builder.build(
            search_filter
        )

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
            payload = point.payload or {}

            results.append(
                SearchResult(
                    score=float(point.score),
                    chunk_id=payload["chunk_id"],
                    paper_name=payload["paper_name"],
                    section_title=payload["section_title"],
                    chunk_text=payload["chunk_text"],
                    page_start=payload["page_start"],
                    page_end=payload["page_end"],
                    token_count=payload["token_count"],
                    images=payload.get("images", []),
                    tables=payload.get("tables", []),
                    metadata=payload,
                )
            )

        return results

    async def retrieve_async(
        self,
        query: QueryEmbedding,
        top_k: int = 10,
        search_filter: SearchFilter | None = None,
    ) -> list[SearchResult]:
        """
        Run the synchronous Qdrant client without blocking
        FastAPI's event loop.
        """

        return await asyncio.to_thread(
            self.retrieve,
            query,
            top_k,
            search_filter,
        )