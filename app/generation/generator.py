from openai import OpenAI

from app.config import (
    OPENAI_API_KEY,
    TEXT_MODEL,
)


class Generator:
    def __init__(self):
        self.client = OpenAI(
            api_key=OPENAI_API_KEY,
        )

    def generate(
        self,
        prompt: str,
    ) -> str:

        response = self.client.chat.completions.create(
            model=TEXT_MODEL,
            temperature=0,

            messages=[
                {
                    "role": "system",
                    "content":
                        "You answer questions from research papers.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        return response.choices[0].message.content