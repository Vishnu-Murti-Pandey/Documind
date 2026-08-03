from fastembed import SparseTextEmbedding
from app.config import QDRANT_SPARSE_TEXT_EMBEDDING


class SparseEncoder:
    def __init__(self):
        self.model = SparseTextEmbedding(
            model_name=QDRANT_SPARSE_TEXT_EMBEDDING
        )

    def encode(
        self,
        text: str,
    ):

        return next(
            self.model.embed([text])
        )