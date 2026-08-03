"""
Generate dense and sparse embeddings for user queries.
"""

import asyncio

from openai import AsyncOpenAI

from app.config import (
    EMBEDDING_MODEL,
    OPENAI_API_KEY,
)
from app.models.query import QueryEmbedding
from app.vectorstore.sparse_encoder import SparseEncoder


class QueryEmbedder:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=OPENAI_API_KEY,
        )

        self.model = EMBEDDING_MODEL
        self.sparse = SparseEncoder()

    async def embed_async(
        self,
        question: str,
    ) -> QueryEmbedding:
        """
        Generate dense and sparse embeddings concurrently.

        Dense embedding:
            Native asynchronous OpenAI request.

        Sparse embedding:
            FastEmbed is blocking, so it runs in a worker thread.
        """

        question = question.strip()

        if not question:
            raise ValueError("Question cannot be empty.")

        dense_request = self.client.embeddings.create(
            model=self.model,
            input=question,
        )

        sparse_request = asyncio.to_thread(
            self.sparse.encode,
            question,
        )

        dense_response, sparse_embedding = await asyncio.gather(
            dense_request,
            sparse_request,
        )

        dense = dense_response.data[0].embedding

        return QueryEmbedding(
            dense=dense,
            sparse_indices=sparse_embedding.indices.tolist(),
            sparse_values=sparse_embedding.values.tolist(),
        )