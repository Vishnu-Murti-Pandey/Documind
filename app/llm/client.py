"""
Reusable OpenAI client.

Every module should use this client instead of creating
its own OpenAI instance.
"""

from openai import OpenAI

from app.config import OPENAI_API_KEY


class OpenAIClient:

    def __init__(self):

        self.client = OpenAI(
            api_key=OPENAI_API_KEY,
        )