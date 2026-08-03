"""
Asynchronous multimodal RAG pipeline.

The pipeline performs:
- query embedding
- hybrid retrieval
- chunk reranking
- figure selection
- context building
- prompt building
- LLM generation

It does not directly persist conversations.
Persistence belongs to ChatService and ConversationMemoryService.
"""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

from app.generation.asset_builder import AssetBuilder
from app.generation.context_builder import ContextBuilder
from app.generation.generator import Generator
from app.generation.prompt_builder import PromptBuilder
from app.models.rag_response import RAGResponse
from app.models.search_filter import SearchFilter
from app.retrieval.citation_builder import CitationBuilder
from app.retrieval.figure_builder import FigureBuilder
from app.retrieval.query_embedder import QueryEmbedder
from app.retrieval.retriever import Retriever
from app.reranking.figure_reranker import FigureReranker
from app.reranking.reranker import Reranker


class RAGPipeline:

    def __init__(self) -> None:
        self.embedder = QueryEmbedder()
        self.retriever = Retriever()
        self.reranker = Reranker()

        self.figure_builder = FigureBuilder()
        self.figure_reranker = FigureReranker()

        self.context_builder = ContextBuilder()
        self.asset_builder = AssetBuilder()
        self.citation_builder = CitationBuilder()
        self.prompt_builder = PromptBuilder()

        self.generator = Generator()

    async def _prepare(
        self,
        question: str,
        search_filter: SearchFilter | None = None,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> tuple[str, list, list, list]:
        """
        Prepare the prompt and structured response metadata.
        """

        question = question.strip()

        if not question:
            raise ValueError(
                "Question cannot be empty."
            )

        # --------------------------------------------------
        # Query embedding
        # --------------------------------------------------

        query = await self.embedder.embed_async(
            question
        )

        # --------------------------------------------------
        # Hybrid retrieval
        # --------------------------------------------------

        results = await self.retriever.retrieve_async(
            query=query,
            top_k=10,
            search_filter=search_filter,
        )

        # --------------------------------------------------
        # Chunk reranking
        # --------------------------------------------------

        results = await self.reranker.rerank_async(
            question=question,
            results=results,
            top_k=5,
        )

        # --------------------------------------------------
        # Build lightweight metadata and context
        # --------------------------------------------------

        raw_figures = self.figure_builder.build(
            results
        )

        tables = self.asset_builder.build_tables(
            results
        )

        context = self.context_builder.build(
            results
        )

        citations = self.citation_builder.build(
            results
        )

        # --------------------------------------------------
        # Figure reranking
        # --------------------------------------------------

        figures = await self.figure_reranker.rerank_async(
            question=question,
            figures=raw_figures,
            top_k=2,
        )

        # --------------------------------------------------
        # Prompt
        # --------------------------------------------------

        prompt = self.prompt_builder.build(
            question=question,
            context=context,
            figures=figures,
            conversation_history=conversation_history,
        )

        if not prompt:
            raise ValueError(
                "PromptBuilder returned an empty prompt."
            )

        return (
            prompt,
            citations,
            figures,
            tables,
        )

    async def ask(
        self,
        question: str,
        search_filter: SearchFilter | None = None,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> RAGResponse:
        """
        Generate a complete non-streaming response.
        """

        (
            prompt,
            citations,
            figures,
            tables,
        ) = await self._prepare(
            question=question,
            search_filter=search_filter,
            conversation_history=conversation_history,
        )

        answer = await self.generator.generate(
            prompt
        )

        return RAGResponse(
            answer=answer,
            citations=citations,
            figures=figures,
            tables=tables,
        )

    async def stream_events(
        self,
        question: str,
        search_filter: SearchFilter | None = None,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Yield internal structured streaming events.

        These are converted to SSE by ChatService.
        """

        question = question.strip()

        if not question:
            raise ValueError(
                "Question cannot be empty."
            )

        # --------------------------------------------------
        # Embedding
        # --------------------------------------------------

        yield {
            "type": "status",
            "data": {
                "stage": "embedding",
                "message": "Understanding your question...",
            },
        }

        query = await self.embedder.embed_async(
            question
        )

        # --------------------------------------------------
        # Retrieval
        # --------------------------------------------------

        yield {
            "type": "status",
            "data": {
                "stage": "retrieval",
                "message": (
                    "Searching relevant paper sections..."
                ),
            },
        }

        results = await self.retriever.retrieve_async(
            query=query,
            top_k=10,
            search_filter=search_filter,
        )

        # --------------------------------------------------
        # Reranking
        # --------------------------------------------------

        yield {
            "type": "status",
            "data": {
                "stage": "reranking",
                "message": (
                    "Ranking the most relevant sections..."
                ),
            },
        }

        results = await self.reranker.rerank_async(
            question=question,
            results=results,
            top_k=5,
        )

        # --------------------------------------------------
        # Context and assets
        # --------------------------------------------------

        yield {
            "type": "status",
            "data": {
                "stage": "context",
                "message": (
                    "Preparing context and supporting assets..."
                ),
            },
        }

        raw_figures = self.figure_builder.build(
            results
        )

        figure_task = asyncio.create_task(
            self.figure_reranker.rerank_async(
                question=question,
                figures=raw_figures,
                top_k=2,
            )
        )

        tables = self.asset_builder.build_tables(
            results
        )

        context = self.context_builder.build(
            results
        )

        citations = self.citation_builder.build(
            results
        )

        figures = await figure_task

        # --------------------------------------------------
        # Prompt
        # --------------------------------------------------

        prompt = self.prompt_builder.build(
            question=question,
            context=context,
            figures=figures,
            conversation_history=conversation_history,
        )

        if not prompt:
            raise ValueError(
                "PromptBuilder returned an empty prompt."
            )

        # --------------------------------------------------
        # Generation
        # --------------------------------------------------

        yield {
            "type": "status",
            "data": {
                "stage": "generation",
                "message": "Generating the answer...",
            },
        }

        async for token in self.generator.stream(
            prompt
        ):
            yield {
                "type": "token",
                "data": {
                    "content": token,
                },
            }

        # --------------------------------------------------
        # Metadata
        # --------------------------------------------------

        yield {
            "type": "metadata",
            "data": {
                "citations": [
                    citation.model_dump(
                        mode="json"
                    )
                    for citation in citations
                ],
                "figures": [
                    figure.model_dump(
                        mode="json"
                    )
                    for figure in figures
                ],
                "tables": [
                    table.model_dump(
                        mode="json"
                    )
                    for table in tables
                ],
            },
        }