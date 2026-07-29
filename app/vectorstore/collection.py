from qdrant_client.models import (
    VectorParams,
    SparseVectorParams,
    Distance,
)

from app.vectorstore.client import VectorClient


COLLECTION_NAME = "research_papers"


class CollectionManager:
    def __init__(self):
        self.client = VectorClient().client

    def create(self):
        collections = self.client.get_collections()

        existing = {
            c.name
            for c in collections.collections
        }

        if COLLECTION_NAME in existing:
            return

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