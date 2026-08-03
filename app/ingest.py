"""
Offline ingestion pipeline.

Pipeline
--------
PDF
    ↓
Parse
    ↓
Chunk
    ↓
Image Enrichment
    ↓
Table Enrichment
    ↓
Embedding
    ↓
Qdrant
"""

from pathlib import Path

from app.chunking.chunker import DocumentChunker
from app.embedding.embedding_builder import EmbeddingBuilder
from app.embedding.embedding_generator import EmbeddingGenerator
from app.enrichment.image_enricher import ImageEnricher
from app.enrichment.table_enricher import TableEnricher
from app.parser.pdf_parser import PDFParser
from app.vectorstore.collection import CollectionManager
from app.vectorstore.store import VectorStore


def ingest(pdf_path: str | Path) -> None:
    """
    Ingest one research paper into Qdrant.
    """

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    paper_name = pdf_path.stem

    print("=" * 80)
    print(f"Ingesting: {paper_name}")
    print("=" * 80)

    # --------------------------------------------------
    # Parse PDF
    # --------------------------------------------------

    parser = PDFParser(pdf_path)

    elements = parser.parse_to_json()

    print(f"Parsed {len(elements)} elements")

    # --------------------------------------------------
    # Chunk Document
    # --------------------------------------------------

    chunker = DocumentChunker()

    chunks = chunker.create_chunks(
        elements=elements,
        paper_name=paper_name,
    )

    print(f"Created {len(chunks)} chunks")

    # --------------------------------------------------
    # Initialize Services
    # --------------------------------------------------

    image_enricher = ImageEnricher()

    table_enricher = TableEnricher()

    embedding_builder = EmbeddingBuilder()

    embedding_generator = EmbeddingGenerator()

    collection_manager = CollectionManager()

    vector_store = VectorStore()

    # --------------------------------------------------
    # Ensure Collection Exists
    # --------------------------------------------------

    collection_manager.create()

    # --------------------------------------------------
    # Process Chunks
    # --------------------------------------------------

    total_chunks = len(chunks)

    for index, chunk in enumerate(chunks, start=1):

        print(
            f"\nProcessing Chunk "
            f"{index}/{total_chunks} "
            f"({chunk['chunk_id']})"
        )

        # ---------------- Images ----------------

        chunk = image_enricher.enrich_chunk(chunk)

        # ---------------- Tables ----------------

        chunk = table_enricher.enrich_chunk(chunk)

        # ---------------- Embedding Document ----------------

        embedding_document = embedding_builder.build_document(
            chunk
        )

        # ---------------- Generate Embedding ----------------

        vector_document = embedding_generator.generate(
            embedding_document
        )

        # ---------------- Store ----------------

        vector_store.insert(vector_document)

        print("✓ Stored in Qdrant")

    print("\n" + "=" * 80)
    print("Pipeline completed successfully.")
    print(f"Stored {total_chunks} chunks.")
    print("=" * 80)


def main():
    ingest(
        "data/input/attention-is-all-you-need-Paper.pdf"
    )


if __name__ == "__main__":
    main()