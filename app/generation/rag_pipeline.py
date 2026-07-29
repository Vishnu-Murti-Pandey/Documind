from app.generation.context_builder import ContextBuilder
from app.generation.generator import Generator
from app.generation.prompt_builder import PromptBuilder
from app.retrieval.query_embedder import QueryEmbedder
from app.retrieval.retriever import Retriever
from app.reranking.reranker import Reranker
from app.retrieval.citation_builder import CitationBuilder
from app.models.rag_response import RAGResponse
from app.models.search_filter import SearchFilter
from app.generation.asset_builder import AssetBuilder
from app.retrieval.figure_builder import FigureBuilder
from app.reranking.figure_reranker import FigureReranker


class RAGPipeline:

    def __init__(self):

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

    def ask(
        self,
        question: str,
        search_filter: SearchFilter | None = None,
    ) -> RAGResponse:

        # --------------------------------------------------
        # Hybrid Retrieval
        # --------------------------------------------------

        query = self.embedder.embed(question)

        results = self.retriever.retrieve(
            query=query,
            top_k=20,
            search_filter=search_filter,
        )

        # --------------------------------------------------
        # Chunk reranking
        # --------------------------------------------------

        results = self.reranker.rerank(
            question=question,
            results=results,
            top_k=5,
        )

        # --------------------------------------------------
        # Figure retrieval + reranking
        # --------------------------------------------------

        figures = self.figure_builder.build(results)

        figures = self.figure_reranker.rerank(
            question=question,
            figures=figures,
            top_k=2,
        )

        # --------------------------------------------------
        # Tables
        # --------------------------------------------------

        tables = self.asset_builder.build_tables(results)

        # --------------------------------------------------
        # Context
        # --------------------------------------------------

        context = self.context_builder.build(results)

        citations = self.citation_builder.build(results)

        # --------------------------------------------------
        # Prompt
        # --------------------------------------------------

        prompt = self.prompt_builder.build(
            question=question,
            context=context,
            figures=figures,
        )

        # --------------------------------------------------
        # LLM
        # --------------------------------------------------

        answer = self.generator.generate(prompt)

        return RAGResponse(
            answer=answer,
            citations=citations,
            figures=figures,
            tables=tables,
        )