import json
import re

from app.ollama_client import RERANK_MODEL, complete

EXCERPT_PREVIEW_CHARS = 300


def _build_prompt(query: str, candidates: list[dict]) -> str:
    excerpts = "\n".join(
        f"[{i}] {c['text'][:EXCERPT_PREVIEW_CHARS]}" for i, c in enumerate(candidates)
    )
    return (
        "You are ranking document excerpts by relevance to a question.\n\n"
        f"Question: {query}\n\n"
        f"Excerpts:\n{excerpts}\n\n"
        "Respond with ONLY a JSON array of the excerpt indices, ordered from "
        "most to least relevant. Example: [2, 0, 3, 1]. Include every index "
        "exactly once."
    )


def _parse_order(response_text: str, count: int) -> list[int]:
    match = re.search(r"\[[^\[\]]*\]", response_text)
    if not match:
        raise ValueError("no JSON array found in rerank response")

    order = json.loads(match.group(0))
    return [i for i in order if isinstance(i, int) and 0 <= i < count]


async def rerank(query: str, candidates: list[dict], top_k: int = 4) -> list[dict]:
    """Reorder candidates by LLM-judged relevance, falling back to their
    original (vector-similarity) order on any failure."""
    if not candidates:
        return []

    try:
        response_text = await complete(_build_prompt(query, candidates), model=RERANK_MODEL)
        order = _parse_order(response_text, len(candidates))

        ranked = [candidates[i] for i in order]
        seen = set(order)
        ranked.extend(c for i, c in enumerate(candidates) if i not in seen)

        return ranked[:top_k]
    except Exception:
        return candidates[:top_k]
