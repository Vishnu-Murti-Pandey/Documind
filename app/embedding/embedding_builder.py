"""
Embedding Builder.

Converts an enriched multimodal chunk into the text
that will be embedded and later stored in the vector DB.
"""

from app.models.embedding_document import EmbeddingDocument


class EmbeddingBuilder:

    def build_document(
        self,
        chunk: dict,
    ) -> EmbeddingDocument:

        parts = []

        # Section
        parts.append(
            f"Section: {chunk['section_title']}"
        )

        # Main text
        parts.append(
            chunk["text"]
        )

        # Images
        for index, image in enumerate(
            chunk["images"],
            start=1,
        ):

            image_block = [
                f"Figure {index}"
            ]

            if image.get("caption"):
                image_block.append(
                    f"Caption: {image['caption']}"
                )

            if image.get("description"):
                image_block.append(
                    f"Description: {image['description']}"
                )

            parts.append(
                "\n".join(image_block)
            )

        # Tables
        for index, table in enumerate(
            chunk["tables"],
            start=1,
        ):

            table_block = [
                f"Table {index}"
            ]

            if table.get("summary"):
                table_block.append(
                    f"Summary: {table['summary']}"
                )

            if table.get("html"):
                table_block.append("HTML:")
                table_block.append(table["html"])

            parts.append(
                "\n".join(table_block)
            )

        embedding_text = "\n\n".join(parts)

        return EmbeddingDocument(
            chunk_id=chunk["chunk_id"],
            paper_name=chunk["paper_name"],
            section_title=chunk["section_title"],
            embedding_text=embedding_text,

            # Store original chunk
            chunk_text=chunk["text"],
            images=chunk["images"],
            tables=chunk["tables"],

            metadata={
                "page_start": chunk["page_start"],
                "page_end": chunk["page_end"],
                "token_count": chunk["token_count"],
                "chunk_text": chunk["text"],
                "images": chunk["images"],
                "tables": chunk["tables"],   
            },
        )