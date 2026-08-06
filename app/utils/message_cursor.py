"""
Opaque cursor helpers for chat-message pagination.
"""

import base64
import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class MessageCursor:
    created_at: datetime
    message_id: UUID


def encode_message_cursor(
    created_at: datetime,
    message_id: UUID,
) -> str:
    payload = {
        "created_at": created_at.isoformat(),
        "message_id": str(message_id),
    }

    encoded = base64.urlsafe_b64encode(
        json.dumps(payload).encode("utf-8")
    )

    return encoded.decode("utf-8")


def decode_message_cursor(
    cursor: str,
) -> MessageCursor:
    try:
        decoded = base64.urlsafe_b64decode(
            cursor.encode("utf-8")
        )

        payload = json.loads(
            decoded.decode("utf-8")
        )

        return MessageCursor(
            created_at=datetime.fromisoformat(
                payload["created_at"]
            ),
            message_id=UUID(
                payload["message_id"]
            ),
        )

    except (
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        raise ValueError(
            "Invalid message cursor."
        ) from exc