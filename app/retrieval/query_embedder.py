"""
Generate embeddings for user queries.
"""

from openai import OpenAI

from app.config import (
    OPENAI_API_KEY,
    EMBEDDING_MODEL,
)
from app.models.query import QueryEmbedding
from app.vectorstore.sparse_encoder import SparseEncoder


class QueryEmbedder:
    def __init__(self):
        self.client = OpenAI(
            api_key=OPENAI_API_KEY,
        )

        self.model = EMBEDDING_MODEL

        self.sparse = SparseEncoder()

    def embed(
        self,
        question: str,
    ) -> QueryEmbedding:

        response = self.client.embeddings.create(
            model=self.model,
            input=question,
        )

        dense = response.data[0].embedding

        sparse = self.sparse.encode(question)

        return QueryEmbedding(
            dense=dense,
            sparse_indices=sparse.indices.tolist(),
            sparse_values=sparse.values.tolist(),
        )