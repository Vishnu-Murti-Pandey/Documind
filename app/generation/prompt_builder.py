"""
Build the final RAG prompt.

The prompt contains:
- previous conversation history
- retrieved research-paper context
- relevant figure information
- the current user question
"""


class PromptBuilder:

    def build(
        self,
        question: str,
        context: str,
        figures: list | None = None,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> str:

        figures = figures or []
        conversation_history = conversation_history or []

        # ============================================================
        # Conversation history
        # ============================================================

        history_context = ""

        if conversation_history:
            history_lines: list[str] = []

            for message in conversation_history:
                role = message.get(
                    "role",
                    "unknown",
                ).strip()

                content = message.get(
                    "content",
                    "",
                ).strip()

                if not content:
                    continue

                role_label = {
                    "user": "User",
                    "assistant": "Assistant",
                    "system": "System",
                }.get(
                    role,
                    role.title(),
                )

                history_lines.append(
                    f"{role_label}:\n{content}"
                )

            if history_lines:
                formatted_history = "\n\n".join(
                    history_lines
                )

                history_context = f"""
========================
Previous Conversation
========================

{formatted_history}
"""

        # ============================================================
        # Figure context
        # ============================================================

        figure_context = ""

        if figures:
            figure_blocks: list[str] = []

            for index, figure in enumerate(
                figures,
                start=1,
            ):
                figure_blocks.append(
                    f"""
Figure {index}

Caption:
{figure.caption or "No caption"}

Description:
{figure.description or "No description"}
""".strip()
                )

            formatted_figures = "\n\n".join(
                figure_blocks
            )

            figure_context = f"""
========================
Relevant Figures
========================

{formatted_figures}
"""

        # ============================================================
        # Final prompt
        # ============================================================

        return f"""
You are an expert research assistant.

Answer the current user question using only:

1. The supplied research-paper context.
2. Relevant figure information.
3. Previous conversation history only when it helps interpret the current question.

The previous conversation is provided for conversational continuity.
It is not an authoritative research source.

If the answer cannot be found in the supplied research-paper context, reply exactly:

"I don't know based on the provided paper."

{history_context}

========================
Research Paper Context
========================

{context}

{figure_context}

========================
Current User Question
========================

{question}

========================
Instructions
========================

1. Answer using only the supplied research-paper context.
2. Use conversation history only to understand references such as:
   - "it"
   - "that"
   - "the previous method"
   - "explain it more simply"
3. Do not treat previous assistant responses as verified research evidence.
4. Do not invent or assume information.
5. If figures are relevant, naturally incorporate them into the explanation.
6. Refer to figures naturally, for example:
   - "As shown in Figure 1..."
   - "Figure 2 illustrates..."
7. Never say:
   - "the figure description says..."
   - "according to the image description..."
   - "based on the provided figure description..."
8. Do not mention image URLs.
9. Do not mention page numbers.
10. Do not generate citations or a Sources section.
11. Write in clear technical language.
12. Use bullet points only when they improve clarity.
""".strip()
