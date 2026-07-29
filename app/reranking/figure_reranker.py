from sentence_transformers import CrossEncoder

from app.models.figure_reference import FigureReference


class FigureReranker:
    def __init__(self):
        self.model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )

    def rerank(
        self,
        question: str,
        figures: list[FigureReference],
        top_k: int = 2,

    ) -> list[FigureReference]:

        if not figures:
            return []

        pairs = []

        for figure in figures:

            text = ""

            if figure.caption:

                text += figure.caption + "\n"

            if figure.description:

                text += figure.description

            pairs.append((question, text))

        scores = self.model.predict(pairs)

        for figure, score in zip(figures, scores):

            figure.score = float(score)

        figures.sort(
            key=lambda x: x.score,
            reverse=True,
        )

        return figures[:top_k]