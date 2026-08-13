from unittest.mock import MagicMock
from types import SimpleNamespace

from qdrant_client.models import PayloadSchemaType

from app.vectorstore.collection import CollectionManager


def test_existing_collection_receives_missing_payload_indexes() -> None:
    manager = CollectionManager.__new__(CollectionManager)
    manager.client = MagicMock()
    manager.client.get_collections.return_value.collections = [
        SimpleNamespace(name="research_papers")
    ]
    manager.client.get_collection.return_value.payload_schema = {
        "paper_name": MagicMock()
    }

    manager.create()

    manager.client.create_collection.assert_not_called()
    calls = manager.client.create_payload_index.call_args_list
    created = {
        call.kwargs["field_name"]: call.kwargs["field_schema"]
        for call in calls
    }
    assert created == {
        "section_title": PayloadSchemaType.KEYWORD,
        "page_start": PayloadSchemaType.INTEGER,
        "page_end": PayloadSchemaType.INTEGER,
    }
