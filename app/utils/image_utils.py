"""
Image helper utilities.
"""

import base64


def bytes_to_base64(
    image_bytes: bytes,
) -> str:
    """
    Convert image bytes to Base64.
    """

    return base64.b64encode(
        image_bytes,
    ).decode("utf-8")