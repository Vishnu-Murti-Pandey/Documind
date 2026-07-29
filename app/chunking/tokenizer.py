"""
Utilities for counting tokens using OpenAI's tokenizer.
"""

import tiktoken


class TokenCounter:
    """
    Wrapper around tiktoken.
    """

    def __init__(self, model: str = "text-embedding-3-small"):

        self.encoding = tiktoken.encoding_for_model(model)

    def count(self, text: str) -> int:
        """
        Return number of tokens in a string.
        """

        return len(self.encoding.encode(text))