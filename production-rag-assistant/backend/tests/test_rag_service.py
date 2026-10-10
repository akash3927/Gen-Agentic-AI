from app.services.rag_service import INSUFFICIENT_ANSWER, build_context, rewrite_query


def test_context_contains_source_metadata():
    context = build_context(
        [{"pdf_name": "guide.pdf", "page_number": 4, "text": "Grounded fact."}], 1_000
    )
    assert "[Source 1: guide.pdf, page 4]" in context
    assert "Grounded fact." in context


def test_context_respects_character_limit():
    context = build_context(
        [{"pdf_name": "long.pdf", "page_number": 1, "text": "x" * 500}], 80
    )
    assert len(context) <= 80


def test_query_rewrite_is_simple_and_visible():
    assert rewrite_query("  What is vector search?  ") == "vector search"


def test_insufficient_context_skips_llm(services):
    _, rag, model = services
    response = rag.answer("unknown astronomy", 5, 1.0, None, True)
    assert response["answer"] == INSUFFICIENT_ANSWER
    assert response["sources"] == []
    assert response["insufficient_context"] is True
    assert model.calls == []
