from app.generation.prompt_builder import PromptBuilder


def test_prompt_requests_stream_safe_plain_text_math() -> None:
    prompt = PromptBuilder().build(
        question="Explain scaled dot-product attention.",
        context="Attention divides dot products by the square root of d-k.",
    )

    assert "1/√dₖ" in prompt
    assert "Never output raw LaTeX commands" in prompt
    assert r"\frac" in prompt
    assert r"\sqrt" in prompt
