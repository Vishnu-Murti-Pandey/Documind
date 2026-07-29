"""
Generate vector embeddings from EmbeddingDocument.
"""

from openai import OpenAI

from app.config import OPENAI_API_KEY, EMBEDDING_MODEL
from app.models.embedding_document import EmbeddingDocument
from app.models.vector_document import VectorDocument


class EmbeddingGenerator:
    def __init__(self):

        self.client = OpenAI(
            api_key=OPENAI_API_KEY,
        )

        self.model = EMBEDDING_MODEL

    def generate(
        self,
        document: EmbeddingDocument,
    ) -> VectorDocument:

        response = self.client.embeddings.create(
            model=self.model,
            input=document.embedding_text,
        )

        embedding = response.data[0].embedding

        return VectorDocument(
            chunk_id=document.chunk_id,
            paper_name=document.paper_name,
            section_title=document.section_title,
            embedding=embedding,
            chunk_text=document.chunk_text,
            images=document.images,
            tables=document.tables,
            metadata=document.metadata,
        )