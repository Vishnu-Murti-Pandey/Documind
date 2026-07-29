"""
Convert Unstructured Elements into JSON serializable dictionaries.
"""

from typing import Any


def _serialize_coordinates(metadata: dict):

    coordinates = metadata.get("coordinates")

    if not coordinates:
        return None

    if "points" in coordinates:
        coordinates["points"] = [
            [float(x), float(y)]
            for x, y in coordinates["points"]
        ]

    return coordinates


def serialize_element(element) -> dict[str, Any]:

    metadata = element.metadata.to_dict()

    category = element.category

    return {

        "id": getattr(element, "id", None),

        "type": category,

        "page": metadata.get("page_number"),

        "text": str(element).strip(),

        "table": (
            {
                "html": getattr(
                    element.metadata,
                    "text_as_html",
                    None,
                )
            }
            if category == "Table"
            else None
        ),

        "image": (
            {
                "base64": metadata.get("image_base64"),
                "mime": metadata.get(
                    "image_mime_type",
                    "image/jpeg",
                ),
                "caption": None,
            }
            if category in ["Image", "ImagePlaceholder"]
            else None
        ),

        "metadata": {

            "filename": metadata.get("filename"),

            "languages": metadata.get("languages"),

            "coordinates": _serialize_coordinates(
                metadata
            ),
        },
    }