from unittest.mock import MagicMock

from app.models.query import QueryEmbedding
from app.retrieval.retriever import Retriever


def test_empty_sparse_query_uses_dense_retrieval() -> None:
    retriever = Retriever.__new__(Retriever)
    retriever.client = MagicMock()
    retriever.filter_builder = MagicMock()
    retriever.filter_builder.build.return_value = None
    retriever.client.query_points.return_value.points = []

    results = retriever.retrieve(
        QueryEmbedding(
            dense=[0.0] * 1536,
            sparse_indices=[],
            sparse_values=[],
        ),
        top_k=5,
    )

    assert results == []
    retriever.client.query_points.assert_called_once_with(
        collection_name="research_papers",
        query=[0.0] * 1536,
        using="dense",
        query_filter=None,
        limit=5,
        with_payload=True,
    )


def test_non_empty_sparse_query_uses_hybrid_retrieval() -> None:
    retriever = Retriever.__new__(Retriever)
    retriever.client = MagicMock()
    retriever.filter_builder = MagicMock()
    retriever.filter_builder.build.return_value = None
    retriever.client.query_points.return_value.points = []

    results = retriever.retrieve(
        QueryEmbedding(
            dense=[0.0] * 1536,
            sparse_indices=[42],
            sparse_values=[1.0],
        )
    )

    assert results == []
    call = retriever.client.query_points.call_args.kwargs
    assert len(call["prefetch"]) == 2
    assert call["query"].fusion.value == "rrf"
