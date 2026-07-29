"""
Post-process Unstructured output.

Responsibilities

1. Remove OCR text that belongs to images.
2. Merge hyphenated words.
3. Insert image placeholders.
4. Preserve captions.
"""

from typing import Any


class DocumentCleaner:

    def clean(
        self,
        elements: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        cleaned = []

        previous_text = None

        for element in elements:

            element_type = element["type"]

            # -------------------------------------------------
            # Images
            # -------------------------------------------------

            if element_type == "Image":

                caption = ""

                if element["image"]:

                    caption = element["image"].get("caption") or ""

                placeholder = {

                    "id": element["id"],

                    "type": "ImagePlaceholder",

                    "page": element["page"],

                    "text": f"[Image: {caption}]",

                    "table": None,

                    "image": element["image"],

                    "metadata": element["metadata"],
                }

                cleaned.append(placeholder)

                previous_text = None

                continue

            # -------------------------------------------------
            # Ignore OCR extracted from images
            # -------------------------------------------------

            if (
                element_type == "UncategorizedText"
                and self._looks_like_image_ocr(element["text"])
            ):
                continue

            # -------------------------------------------------
            # Merge hyphenated words
            # -------------------------------------------------

            if (
                previous_text
                and previous_text["type"] == "NarrativeText"
                and previous_text["text"].endswith("-")
                and element_type == "NarrativeText"
            ):

                previous_text["text"] = (
                    previous_text["text"][:-1]
                    + element["text"]
                )

                continue

            cleaned.append(element)

            previous_text = element

        return cleaned

    def _looks_like_image_ocr(
        self,
        text: str,
    ) -> bool:
        """
        Heuristic for removing OCR that
        comes from diagrams.
        """

        if len(text) < 10:
            return False

        keywords = [

            "Add & Norm",

            "Feed Forward",

            "Input Embedding",

            "Output Embedding",

            "Positional Encoding",

            "Multi-Head Attention",

            "Output Probabilities",
        ]

        matches = 0

        lower = text.lower()

        for keyword in keywords:

            if keyword.lower() in lower:

                matches += 1

        return matches >= 2