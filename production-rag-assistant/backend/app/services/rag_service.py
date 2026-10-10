import re

from app.services.openai_client import EmbeddingProvider, LanguageModel
from app.services.vector_store import ChromaVectorStore

INSUFFICIENT_ANSWER = "I don't know based on the indexed documents."
GROUNDING_INSTRUCTIONS = """You are a grounded document question-answering assistant.
Answer only from the supplied context. Do not use outside knowledge or invent facts.
The context blocks have source labels like [Source 1]. Cite those labels inline when useful.
If the context does not support an answer, respond exactly: I don't know based on the indexed documents.
Keep the answer concise and directly address the question."""


def rewrite_query(question: str) -> str:
    """Simple deterministic rewrite: normalize wording and add useful terms from the question."""
    normalized = re.sub(r"\s+", " ", question).strip()
    prefixes = ("what is ", "what are ", "how does ", "tell me about ")
    lowered = normalized.lower()
    for prefix in prefixes:
        if lowered.startswith(prefix):
            normalized = normalized[len(prefix) :]
            break
    return normalized.rstrip(" ?.!") or question


def rerank(question: str, candidates: list[dict]) -> list[dict]:
    """Blend vector similarity with transparent lexical token overlap."""
    query_terms = set(re.findall(r"[a-z0-9]+", question.lower()))
    for item in candidates:
        chunk_terms = set(re.findall(r"[a-z0-9]+", item["text"].lower()))
        lexical = len(query_terms & chunk_terms) / max(1, len(query_terms))
        item["rerank_score"] = 0.85 * item["score"] + 0.15 * lexical
    return sorted(candidates, key=lambda item: item["rerank_score"], reverse=True)


def build_context(sources: list[dict], max_characters: int) -> str:
    blocks: list[str] = []
    used = 0
    for index, source in enumerate(sources, start=1):
        block = (
            f"[Source {index}: {source['pdf_name']}, page {source['page_number']}]\n"
            f"{source['text']}"
        )
        remaining = max_characters - used
        if remaining <= 0:
            break
        blocks.append(block[:remaining])
        used += len(block) + 2
    return "\n\n".join(blocks)


class RagService:
    def __init__(
        self,
        embedder: EmbeddingProvider,
        language_model: LanguageModel,
        vector_store: ChromaVectorStore,
        max_context_characters: int = 16_000,
    ) -> None:
        self.embedder = embedder
        self.language_model = language_model
        self.vector_store = vector_store
        self.max_context_characters = max_context_characters

    def answer(
        self,
        question: str,
        top_k: int,
        threshold: float,
        document_ids: list[str] | None,
        use_rewrite: bool,
    ) -> dict:
        # question -> rewrite -> embed -> retrieve -> threshold -> rerank -> context -> LLM
        retrieval_query = rewrite_query(question) if use_rewrite else question
        query_vector = self.embedder.embed([retrieval_query])[0]
        candidates = self.vector_store.search(query_vector, max(top_k * 3, top_k), document_ids)
        relevant = [item for item in candidates if item["score"] >= threshold]
        sources = rerank(question, relevant)[:top_k]

        if not sources:
            return {
                "answer": INSUFFICIENT_ANSWER,
                "sources": [],
                "retrieval_query": retrieval_query,
                "insufficient_context": True,
            }

        context = build_context(sources, self.max_context_characters)
        prompt = f"Context:\n{context}\n\nQuestion: {question}\n\nGrounded answer:"
        answer = self.language_model.generate(GROUNDING_INSTRUCTIONS, prompt)
        insufficient = answer.strip() == INSUFFICIENT_ANSWER
        return {
            "answer": answer,
            "sources": sources,
            "retrieval_query": retrieval_query,
            "insufficient_context": insufficient,
        }
