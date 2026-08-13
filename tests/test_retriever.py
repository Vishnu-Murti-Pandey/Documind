from unittest.mock import MagicMock

from httpx import Headers
from qdrant_client.http.exceptions import UnexpectedResponse

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


def test_sparse_query_is_sorted_and_duplicate_indices_are_combined() -> None:
    vector = Retriever._normalized_sparse_vector(
        QueryEmbedding(
            dense=[0.0] * 1536,
            sparse_indices=[9, 2, 9],
            sparse_values=[0.5, 1.0, 0.25],
        )
    )

    assert vector is not None
    assert vector.indices == [2, 9]
    assert vector.values == [1.0, 0.75]


def test_hybrid_bad_request_retries_with_dense_retrieval() -> None:
    retriever = Retriever.__new__(Retriever)
    retriever.client = MagicMock()
    retriever.filter_builder = MagicMock()
    retriever.filter_builder.build.return_value = None
    bad_request = UnexpectedResponse(
        status_code=400,
        reason_phrase="Bad Request",
        content=b'{"status":{"error":"invalid sparse vector"}}',
        headers=Headers(),
    )
    successful_response = MagicMock()
    successful_response.points = []
    retriever.client.query_points.side_effect = [
        bad_request,
        successful_response,
    ]

    results = retriever.retrieve(
        QueryEmbedding(
            dense=[0.0] * 1536,
            sparse_indices=[42],
            sparse_values=[1.0],
        ),
        top_k=5,
    )

    assert results == []
    assert retriever.client.query_points.call_count == 2
    fallback = retriever.client.query_points.call_args_list[1].kwargs
    assert fallback["using"] == "dense"
    assert fallback["limit"] == 5
