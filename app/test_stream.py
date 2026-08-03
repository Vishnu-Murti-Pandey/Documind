import asyncio

from app.services.chat_service import ChatService
from app.api.schemas.chat_request import ChatRequest


async def main() -> None:
    service = ChatService()

    request = ChatRequest(
        message="Explain Multi Head Attention.",
        conversation_id="demo",
        filter=None,
    )

    async for event in service.stream_chat(request):
        print(event, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
