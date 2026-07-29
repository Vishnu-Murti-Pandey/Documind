from sentence_transformers import CrossEncoder
from app.retrieval.search_results import SearchResult


class Reranker:
    def __init__(self):
        self.model = CrossEncoder(
            "BAAI/bge-reranker-v2-m3"
        )

    def rerank(
        self,
        question: str,
        results: list[SearchResult],
        top_k: int = 5,
    ) -> list[SearchResult]:

        if not results:
            return []

        pairs = [
            (question, result.chunk_text)
            for result in results
        ]

        scores = self.model.predict(
            pairs
        )

        ranked = sorted(
            zip(results, scores),
            key=lambda x: x[1],
            reverse=True,
        )

        return [
            result
            for result, _ in ranked[:top_k]
        ]