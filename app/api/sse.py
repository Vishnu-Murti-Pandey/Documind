"""
Server-Sent Event formatting utilities.
"""

import json
from typing import Any


def sse_event(
    event: str,
    data: Any,
) -> str:
    """
    Format one Server-Sent Event.

    Example output:

    event: token
    data: {"content": "Hello"}

    """

    encoded_data = json.dumps(
        data,
        ensure_ascii=False,
        default=str,
    )

    return (
        f"event: {event}\n"
        f"data: {encoded_data}\n\n"
    )