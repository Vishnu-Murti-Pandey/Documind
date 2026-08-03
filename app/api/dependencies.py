"""FastAPI dependencies for lazily initialized application services."""

from functools import lru_cache

from app.services.chat_service import ChatService


@lru_cache
def get_chat_service() -> ChatService:
    """Create the model-backed chat service only when it is first used."""

    return ChatService()
