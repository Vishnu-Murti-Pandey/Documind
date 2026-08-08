import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.db.models.chat_message import MessageRole
from app.services.conversation_memory import ConversationMemoryService


class ConversationMemoryServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_prepare_populates_history_and_llm_history(self) -> None:
        session = AsyncMock()
        service = ConversationMemoryService(session=session, history_limit=10)

        conversation = SimpleNamespace(
            id="internal-id",
            public_id="public-id",
            paper_name="paper",
        )
        messages = [
            SimpleNamespace(
                role=MessageRole.USER,
                content="What is attention?",
            ),
        ]

        service.conversation_repository.get_or_create = AsyncMock(
            return_value=(conversation, False),
        )
        service.message_repository.list_recent = AsyncMock(
            return_value=messages,
        )

        context = await service.prepare(
            public_id="public-id",
            paper_name="paper",
        )

        self.assertIs(context.conversation, conversation)
        self.assertEqual(context.history, messages)
        self.assertEqual(
            context.llm_history,
            [{"role": "user", "content": "What is attention?"}],
        )
        self.assertFalse(context.is_new_conversation)


if __name__ == "__main__":
    unittest.main()
