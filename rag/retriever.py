# rag/retriever.py

from typing import List, Dict, Any, Optional
from rag.vector_store import VectorStore


# --------------------------------------------------
# QUERY EXPANSION
# --------------------------------------------------
def expand_query(query: str) -> List[str]:
    """
    Expand query into multiple variations
    """
    query = query.lower()

    expansions = [query]

    # Simple domain-specific expansions
    if "resistor" in query:
        expansions.extend(["r", "ohm", "res"])
    if "capacitor" in query:
        expansions.extend(["cap", "uf", "nf"])
    if "power" in query:
        expansions.extend(["vcc", "gnd", "supply"])
    if "signal" in query:
        expansions.extend(["net", "connection"])

    return list(set(expansions))


# --------------------------------------------------
# SCORING
# --------------------------------------------------
def score_result(query: str, text: str) -> int:
    """
    Token overlap scoring
    """
    q_tokens = set(query.lower().split())
    t_tokens = set(text.lower().split())

    return len(q_tokens & t_tokens)


# --------------------------------------------------
# MAIN RETRIEVAL
# --------------------------------------------------
def retrieve(
    query: str,
    store: VectorStore,
    top_k: int = 5,
    filter_meta: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Enhanced retrieval pipeline
    """

    if not query or not store:
        return []

    queries = expand_query(query)

    results = []

    # Collect results from expanded queries
    for q in queries:
        hits = store.search(q, top_k=top_k * 2, filter_meta=filter_meta)

        for h in hits:
            score = score_result(query, h["text"])

            results.append({
                "text": h["text"],
                "metadata": h.get("metadata", {}),
                "score": score
            })

    # --------------------------------------------------
    # DEDUPLICATE (by text)
    # --------------------------------------------------
    unique = {}
    for r in results:
        key = r["text"]

        if key not in unique or unique[key]["score"] < r["score"]:
            unique[key] = r

    results = list(unique.values())

    # --------------------------------------------------
    # SORT BY SCORE
    # --------------------------------------------------
    results.sort(key=lambda x: x["score"], reverse=True)

    return results[:top_k]


# --------------------------------------------------
# CONTEXT BUILDER
# --------------------------------------------------
def build_context(docs: List[Dict[str, Any]], max_chars: int = 1500) -> str:
    """
    Convert docs → context string for LLM
    """

    context_parts = []
    total_len = 0

    for d in docs:
        text = d["text"]

        if total_len + len(text) > max_chars:
            break

        context_parts.append(text)
        total_len += len(text)

    return "\n".join(context_parts)


# --------------------------------------------------
# FILTER BY TYPE
# --------------------------------------------------
def retrieve_by_type(
    query: str,
    store: VectorStore,
    doc_type: str,
    top_k: int = 5
):
    """
    Retrieve only specific document type
    """
    return retrieve(
        query,
        store,
        top_k=top_k,
        filter_meta={"type": doc_type}
    )


# --------------------------------------------------
# DEBUG
# --------------------------------------------------
if __name__ == "__main__":
    from rag.vector_store import VectorStore

    store = VectorStore()

    store.add("R1 is a resistor", {"type": "component"})
    store.add("C1 is a capacitor", {"type": "component"})
    store.add("VCC connects R1 and C1", {"type": "net"})

    results = retrieve("resistor", store)

    print("Results:")
    for r in results:
        print(r)
