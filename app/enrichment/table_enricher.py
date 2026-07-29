"""
Table Enrichment.

Responsible for converting extracted HTML tables into
retrieval-friendly semantic descriptions using GPT-4.1.
"""

from app.llm.client import OpenAIClient


class TableEnricher:
    """
    Enrich tables extracted by Unstructured.
    """

    def __init__(self):

        self.openai = OpenAIClient().client

    def enrich_chunk(
        self,
        chunk: dict,
    ) -> dict:
        """
        Enrich every table inside a chunk.
        """

        tables = chunk.get("tables", [])

        for table in tables:

            html = table.get("html")

            if not html:
                continue

            description = self.describe_table(html)

            table["description"] = description

        return chunk

    def describe_table(
        self,
        html: str,
    ) -> str:
        """
        Generate a semantic description of a table.
        """

        prompt = f"""
            You are analyzing a table extracted from a research paper.

            Below is the table in HTML format.

            {html}

            Your task:

            1. Explain what this table compares.
            2. Identify important rows and columns.
            3. Mention the major findings.
            4. Mention the highest/best values if obvious.
            5. Mention trends or comparisons.
            6. Produce a concise description suitable for semantic retrieval.

            Do NOT copy the entire table.

            Return only the description.
        """

        response = self.openai.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return response.choices[0].message.content