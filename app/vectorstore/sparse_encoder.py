from fastembed import SparseTextEmbedding
from app.config import QDRANT_Sparse_Text_Embedding


class SparseEncoder:
    def __init__(self):
        self.model = SparseTextEmbedding(
            model_name=QDRANT_Sparse_Text_Embedding
        )

    def encode(
        self,
        text: str,
    ):

        return next(
            self.model.embed([text])
        )