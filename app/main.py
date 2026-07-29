from pathlib import Path

from app.chunking.chunker import DocumentChunker
from app.embedding.embedding_builder import EmbeddingBuilder
from app.embedding.embedding_generator import EmbeddingGenerator
from app.enrichment.image_enricher import ImageEnricher
from app.enrichment.table_enricher import TableEnricher
from app.parser.pdf_parser import PDFParser
from app.vectorstore.collection import CollectionManager
from app.vectorstore.store import VectorStore


def main():

    # --------------------------------------------------
    # Input PDF
    # --------------------------------------------------

    pdf_path = Path(
        "data/input/attention-is-all-you-need-Paper.pdf"
    )

    paper_name = pdf_path.stem

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
    # Create Collection (Only if it doesn't exist)
    # --------------------------------------------------

    collection_manager.create()

    # --------------------------------------------------
    # Process Every Chunk
    # --------------------------------------------------

    for index, chunk in enumerate(chunks, start=1):

        print(
            f"\nProcessing Chunk {index}/{len(chunks)} "
            f"({chunk['chunk_id']})"
        )

        # Enrich Images
        chunk = image_enricher.enrich_chunk(chunk)

        # Enrich Tables
        chunk = table_enricher.enrich_chunk(chunk)

        # Build Embedding Document
        embedding_document = embedding_builder.build_document(
            chunk
        )

        # Generate Embedding
        vector_document = embedding_generator.generate(
            embedding_document
        )

        # Store in Qdrant
        vector_store.insert(vector_document)

        print("✓ Stored in Qdrant")

    print("\n========================================")
    print("Pipeline completed successfully.")
    print(f"Total chunks stored: {len(chunks)}")
    print("========================================")


if __name__ == "__main__":
    main()