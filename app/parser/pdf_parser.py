"""
PDF parser using Unstructured.

This module is responsible for:
1. Parsing a PDF.
2. Returning the raw Unstructured elements.
3. Attaching FigureCaption elements to the preceding Image.
"""

from pathlib import Path

import unstructured_pytesseract
from unstructured.partition.pdf import partition_pdf
from app.preprocessing.document_cleaner import DocumentCleaner

from app.config import IMAGE_DIR
from app.parser.serializer import serialize_element
from app.utils.dependency_checker import check_tesseract


class PDFParser:
    """
    Wrapper around Unstructured's partition_pdf().
    """

    def __init__(self, pdf_path: Path):

        self.pdf_path = pdf_path

    # Configure Tesseract once during initialization.
    # We don't rely on PATH because installations
    # may differ across machines.
    unstructured_pytesseract.pytesseract.tesseract_cmd = (
        check_tesseract()
    )

    def parse(self):
        """
        Parse the PDF into Unstructured elements.
        """

        return partition_pdf(
            filename=str(self.pdf_path),
            strategy="hi_res",

            infer_table_structure=True,
            extract_images_in_pdf=True,
            extract_image_block_to_payload=True,
        )

    def parse_to_json(self) -> list[dict]:
        """
        Parse PDF and return our internal JSON schema.

        Also associates FigureCaption with the
        immediately preceding Image element.
        """

        raw_elements = self.parse() 

        elements = [
            serialize_element(element)
            for element in raw_elements
        ]

        self._attach_image_captions(elements)

        cleaner = DocumentCleaner()

        elements = cleaner.clean(elements)

        return elements

    def _attach_image_captions(
        self,
        elements: list[dict],
    ) -> None:
        """
        Attach FigureCaption text to the nearest
        preceding Image on the same page.

        Research papers generally have:

            Image
            FigureCaption

        but sometimes there may be a few OCR text
        blocks between them, so we search backwards.
        """

        MAX_LOOKBACK = 5

        for index, element in enumerate(elements):

            if element["type"] != "FigureCaption":
                continue

            caption = element["text"].strip()

            if not caption:
                continue

            page = element["page"]

            for previous in range(index - 1, max(index - MAX_LOOKBACK, -1), -1):

                candidate = elements[previous]

                if candidate["page"] != page:
                    break

                if candidate["image"] is not None:

                    candidate["image"]["caption"] = caption

                    break