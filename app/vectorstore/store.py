"""
Insert vectors into Qdrant.
"""

import uuid

from qdrant_client.models import (
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PointStruct
)

from app.models.vector_document import VectorDocument
from app.vectorstore.client import VectorClient
from app.vectorstore.collection import COLLECTION_NAME
from qdrant_client.models import SparseVector


class VectorStore:

    def __init__(self):

        self.client = VectorClient().client
        self._sparse = None

    @property
    def sparse(self):
        """Initialize sparse encoding only for vector insertion."""

        if self._sparse is None:
            from app.vectorstore.sparse_encoder import SparseEncoder

            self._sparse = SparseEncoder()

        return self._sparse

    def insert(
        self,
        document: VectorDocument,
    ) -> None:

        # ------------------------------------------
        # Generate sparse embedding
        # ------------------------------------------

        sparse_embedding = self.sparse.encode(
            document.chunk_text
        )

        payload = {
            "chunk_id": document.chunk_id,
            "paper_name": document.paper_name,
            "section_title": document.section_title,
            "chunk_text": document.chunk_text,
            "page_start": document.metadata["page_start"],
            "page_end": document.metadata["page_end"],
            "token_count": document.metadata["token_count"],
            "images": document.images,
            "tables": document.tables,
        }

        point = PointStruct(
            id=str(
                uuid.uuid5(
                    uuid.NAMESPACE_DNS,
                    f"{document.paper_name}:{document.chunk_id}",
                )
            ),
            vector={
                "dense": document.embedding,
                "sparse": SparseVector(
                    indices=sparse_embedding.indices.tolist(),
                    values=sparse_embedding.values.tolist(),
                ),
            },
            payload=payload,
        )

        self.client.upsert(
            collection_name=COLLECTION_NAME,
            wait=True,
            points=[point],
        )
        
    def delete_by_paper_name(
        self,
        paper_name: str,
    ) -> None:
        """
        Delete every vector belonging to one paper.

        Cleanup is idempotent: a fresh Qdrant project has no collection yet,
        and deleting a stale PostgreSQL document must still succeed.
        """

        if not self.client.collection_exists(
            collection_name=COLLECTION_NAME,
        ):
            return

        self.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(
                            key="paper_name",
                            match=MatchValue(
                                value=paper_name
                            ),
                        )
                    ]
                )
            ),
            wait=True,
        )
