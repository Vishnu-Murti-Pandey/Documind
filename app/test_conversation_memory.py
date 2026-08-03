import asyncio

from app.db.session import AsyncSessionFactory
from app.services.conversation_memory import (
    ConversationMemoryService,
)


async def main() -> None:
    async with AsyncSessionFactory() as session:
        memory = ConversationMemoryService(
            session=session,
            history_limit=10,
        )

        context = await memory.prepare(
            public_id="memory-test",
        )

        print(
            "Conversation:",
            context.conversation.public_id,
        )

        print(
            "New conversation:",
            context.is_new_conversation,
        )

        print(
            "Previous messages:",
            len(context.history),
        )

        if context.is_new_conversation:
            await memory.set_initial_title(
                conversation=context.conversation,
                user_message=(
                    "Explain multi-head attention."
                ),
            )

        await memory.save_user_message(
            conversation=context.conversation,
            content="Explain multi-head attention.",
        )

        await memory.save_assistant_message(
            conversation=context.conversation,
            content=(
                "Multi-head attention runs multiple "
                "attention heads in parallel."
            ),
            citations=[],
            figures=[],
            tables=[],
        )

        history = await memory.load_llm_history(
            conversation=context.conversation,
        )

        for message in history:
            print(
                message["role"],
                "->",
                message["content"],
            )


if __name__ == "__main__":
    asyncio.run(main())