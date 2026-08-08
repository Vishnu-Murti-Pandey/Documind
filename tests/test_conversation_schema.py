import unittest
from datetime import UTC, datetime

from app.api.schemas.conversation import ConversationDetailResponse


class ConversationDetailResponseTests(unittest.TestCase):
    def test_serializes_bound_document_name(self) -> None:
        response = ConversationDetailResponse(
            conversation_id="conversation-id",
            title="Document chat",
            summary=None,
            paper_name="bound-document",
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        self.assertEqual(
            response.model_dump()["paper_name"],
            "bound-document",
        )


if __name__ == "__main__":
    unittest.main()
