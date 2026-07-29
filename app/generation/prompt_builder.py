from app.models.figure_reference import FigureReference

class PromptBuilder:

    def build(
        self,
        question: str,
        context: str,
        figures: list[FigureReference],
    ) -> str:

        figure_context = ""

        if figures:

            figure_context = "Relevant Figures\n----------------\n"

            for index, figure in enumerate(figures, start=1):

                figure_context += f"""
                Figure {index}

                Caption:
                {figure.caption}

                Description:
                {figure.description}

                Storage:
                {figure.storage["object_name"]}

                """

                return f"""
                You are answering questions from a research paper.

                Use ONLY the supplied context.

                If the answer cannot be answered from the context,
                reply that you don't know.

                Context
                -------
                {context}

                {figure_context}

                Question
                --------
                {question}

                Write a complete Markdown answer.

                If a figure is relevant,
                refer to it naturally in the answer.

                Do NOT invent figures.

                Do NOT invent citations.

                Do NOT generate a Sources section.
                """