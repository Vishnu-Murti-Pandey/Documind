"""
Cross-encoder reranker for retrieved text chunks.
"""

import asyncio

from sentence_transformers import CrossEncoder

from app.retrieval.search_results import SearchResult


class Reranker:
    def __init__(self) -> None:
        self.model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )

        # Protect the shared model instance from simultaneous predict calls.
        self._lock = asyncio.Lock()

    def rerank(
        self,
        question: str,
        results: list[SearchResult],
        top_k: int = 5,
    ) -> list[SearchResult]:
        """
        Rerank retrieved chunks synchronously.
        """

        if not results:
            return []

        pairs = [
            (
                question,
                result.chunk_text,
            )
            for result in results
        ]

        scores = self.model.predict(
            pairs,
            batch_size=32,
            show_progress_bar=False,
        )

        ranked = sorted(
            zip(results, scores),
            key=lambda item: float(item[1]),
            reverse=True,
        )

        reranked_results: list[SearchResult] = []

        for result, score in ranked[:top_k]:
            # Preserve the cross-encoder score for later inspection.
            result.score = float(score)
            reranked_results.append(result)

        return reranked_results

    async def rerank_async(
        self,
        question: str,
        results: list[SearchResult],
        top_k: int = 5,
    ) -> list[SearchResult]:
        """
        Run CPU-intensive reranking in a worker thread.
        """

        if not results:
            return []

        async with self._lock:
            return await asyncio.to_thread(
                self.rerank,
                question,
                results,
                top_k,
            )