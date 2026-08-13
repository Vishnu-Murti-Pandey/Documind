from qdrant_client.models import (
    PayloadSchemaType,
    VectorParams,
    SparseVectorParams,
    Distance,
)

from app.vectorstore.client import VectorClient


COLLECTION_NAME = "research_papers"

PAYLOAD_INDEXES = {
    "paper_name": PayloadSchemaType.KEYWORD,
    "section_title": PayloadSchemaType.KEYWORD,
    "page_start": PayloadSchemaType.INTEGER,
    "page_end": PayloadSchemaType.INTEGER,
}


class CollectionManager:
    def __init__(self):
        self.client = VectorClient().client

    def create(self):
        collections = self.client.get_collections()

        existing = {
            c.name
            for c in collections.collections
        }

        if COLLECTION_NAME not in existing:
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config={
                    "dense": VectorParams(
                        size=1536,
                        distance=Distance.COSINE,
                    )
                },
                sparse_vectors_config={
                    "sparse": SparseVectorParams()
                },
            )

        self.ensure_payload_indexes()

    def ensure_payload_indexes(self) -> None:
        """Create indexes required by document and page filters."""

        collection = self.client.get_collection(
            collection_name=COLLECTION_NAME,
        )
        indexed_fields = set(collection.payload_schema)

        for field_name, field_schema in PAYLOAD_INDEXES.items():
            if field_name in indexed_fields:
                continue

            self.client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name=field_name,
                field_schema=field_schema,
                wait=True,
            )
