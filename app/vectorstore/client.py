from qdrant_client import QdrantClient

from app.config import QDRANT_URL


class VectorClient:
    def __init__(self):
        self.client = QdrantClient(url=QDRANT_URL)