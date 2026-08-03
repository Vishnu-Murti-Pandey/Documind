"""
Cross-encoder reranker for retrieved figures.
"""

import asyncio

from sentence_transformers import CrossEncoder

from app.models.figure_reference import FigureReference


class FigureReranker:
    def __init__(self) -> None:
        self.model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )

        self._lock = asyncio.Lock()

    def rerank(
        self,
        question: str,
        figures: list[FigureReference],
        top_k: int = 2,
    ) -> list[FigureReference]:
        """
        Rerank figures using their caption and semantic description.
        """

        if not figures:
            return []

        pairs: list[tuple[str, str]] = []

        for figure in figures:
            text_parts: list[str] = []

            if figure.caption:
                text_parts.append(figure.caption)

            if figure.description:
                text_parts.append(figure.description)

            figure_text = "\n".join(text_parts).strip()

            if not figure_text:
                figure_text = "Research paper figure"

            pairs.append(
                (
                    question,
                    figure_text,
                )
            )

        scores = self.model.predict(
            pairs,
            batch_size=32,
            show_progress_bar=False,
        )

        for figure, score in zip(figures, scores):
            figure.score = float(score)

        return sorted(
            figures,
            key=lambda figure: figure.score,
            reverse=True,
        )[:top_k]

    async def rerank_async(
        self,
        question: str,
        figures: list[FigureReference],
        top_k: int = 2,
    ) -> list[FigureReference]:
        """
        Run figure reranking in a worker thread.
        """

        if not figures:
            return []

        async with self._lock:
            return await asyncio.to_thread(
                self.rerank,
                question,
                figures,
                top_k,
            )