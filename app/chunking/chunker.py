"""
Section-based chunker.

Each Title starts a new chunk.
Everything until the next Title belongs to that chunk.

No token splitting.
"""

from typing import Any

from app.chunking.tokenizer import TokenCounter

SKIP_TYPES = {
    "Footer",
    "Header",
    "PageNumber",
}


class DocumentChunker:

    def __init__(self):
        self.counter = TokenCounter()

    def create_chunks(
        self,
        elements: list[dict[str, Any]],
        paper_name: str,
    ) -> list[dict]:

        chunks = []

        current_chunk = None

        chunk_index = 1

        for element in elements:
            element_type = element["type"]

            # Skip noisy elements
            if element_type in SKIP_TYPES:
                continue

            text = element["text"].strip()

            if not text and element_type not in [
                "ImagePlaceholder",
                "Image",
                "Table",
            ]:
                continue

            # -----------------------------
            # Start New Section
            # -----------------------------

            if element_type == "Title":

                if current_chunk:

                    current_chunk["text"] = "\n\n".join(
                        current_chunk["text"]
                    )

                    current_chunk["token_count"] = self.counter.count(
                        current_chunk["text"]
                    )

                    chunks.append(current_chunk)

                current_chunk = {

                    "chunk_id": f"chunk_{chunk_index:04d}",

                    "paper_name": paper_name,

                    "section_title": text,

                    "page_start": element["page"],

                    "page_end": element["page"],

                    "text": [text],

                    "tables": [],

                    "images": [],

                    "element_types": ["Title"],
                }

                chunk_index += 1

                continue

            if current_chunk is None:
                continue

            current_chunk["page_end"] = element["page"]

            current_chunk["element_types"].append(element_type)

            # -----------------------------
            # Image Placeholder
            # -----------------------------

            if element_type == "ImagePlaceholder":

                figure_no = len(current_chunk["images"]) + 1

                current_chunk["text"].append(
                    f"[[FIGURE_{figure_no}]]"
                )

            # -----------------------------
            # Image
            # -----------------------------
            
            if element["image"]:

                current_chunk["images"].append(
                    element["image"]
                )

            # -----------------------------
            # Figure Caption
            # -----------------------------

            if element_type == "FigureCaption":

                current_chunk["text"].append(text)

                if current_chunk["images"]:

                    current_chunk["images"][-1]["caption"] = text

                continue

            # -----------------------------
            # Normal Text
            # -----------------------------

            if text:
                current_chunk["text"].append(text)

            # -----------------------------
            # Table
            # -----------------------------

            if element["table"]:

                current_chunk["tables"].append(
                    element["table"]
                )

        if current_chunk:

            current_chunk["text"] = "\n\n".join(
                current_chunk["text"]
            )

            current_chunk["token_count"] = self.counter.count(
                current_chunk["text"]
            )

            chunks.append(current_chunk)

        return chunks