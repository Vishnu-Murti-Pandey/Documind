from app.generation.rag_pipeline import RAGPipeline
from app.models.search_filter import SearchFilter

def main():
    rag = RAGPipeline()

    question = "Explain attention."

    response = rag.ask(
        question=question,
        search_filter=SearchFilter(
            page_start=3,
            page_end=5,
        ),
    )

    print("\n")
    print("=" * 80)
    print("ANSWER")
    print("=" * 80)
    print(response.answer)

    print("\nFigures")
    print(response.figures)

    print("\nTables")
    print(response.tables)

    print("\nCitations")
    print(response.citations)



if __name__ == "__main__":
    main()