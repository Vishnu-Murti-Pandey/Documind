"""
LLM Generator.

Uses AsyncOpenAI for:
1. Non-streaming asynchronous generation.
2. Asynchronous token streaming.
"""

from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from app.config import (
    OPENAI_API_KEY,
    TEXT_MODEL,
)


class Generator:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=OPENAI_API_KEY,
        )

    def _messages(
        self,
        prompt: str,
    ) -> list[dict[str, str]]:
        """
        Build the messages sent to OpenAI.
        """

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        return [
            {
                "role": "system",
                "content": (
                    "You answer questions from research papers "
                    "using only the supplied context."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

    async def generate(
        self,
        prompt: str,
    ) -> str:
        """
        Generate the complete answer asynchronously.
        """

        response = await self.client.chat.completions.create(
            model=TEXT_MODEL,
            temperature=0,
            messages=self._messages(prompt),
        )

        return response.choices[0].message.content or ""

    async def stream(
        self,
        prompt: str,
    ) -> AsyncGenerator[str, None]:
        """
        Stream answer text as it is generated.
        """

        stream = await self.client.chat.completions.create(
            model=TEXT_MODEL,
            temperature=0,
            stream=True,
            messages=self._messages(prompt),
        )

        async for chunk in stream:
            if not chunk.choices:
                continue

            token = chunk.choices[0].delta.content

            if token:
                yield token