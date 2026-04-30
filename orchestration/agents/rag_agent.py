# orchestration/agents/rag_agent.py

from typing import Dict, Any, List

from rag.vector_store import VectorStore
from rag.ingestion import design_to_docs


# ==================================================
# GLOBAL STORE (shared across runs)
# ==================================================
STORE = VectorStore()


# ==================================================
# CLEAR STORE (OPTIONAL)
# ==================================================
def _reset_store_if_needed(state):
    """
    Reset store if new session or requested
    """
    if state.get("reset_rag", False):
        STORE.clear()
        state.log("RAG store cleared")


# ==================================================
# INCREMENTAL INGESTION CHECK
# ==================================================
def _should_ingest(state: Dict[str, Any]) -> bool:
    """
    Avoid duplicate ingestion if already done
    """
    return not state.get("rag_ingested", False)


# ==================================================
# BUILD CONTEXT SUMMARY
# ==================================================
def _build_context_summary(docs: List[Dict[str, Any]]) -> Dict[str, int]:
    summary = {}

    for d in docs:
        doc_type = d.get("metadata", {}).get("type", "unknown")
        summary[doc_type] = summary.get(doc_type, 0) + 1

    return summary


# ==================================================
# MAIN AGENT
# ==================================================
def run_rag(state):
    """
    RAG Agent:
    - Converts design into documents
    - Stores in vector DB
    - Prepares context for AI agents
    """

    try:
        state.set_stage("rag")
        state.log("RAG ingestion started")

        design = state.get_design()

        if not design:
            raise ValueError("No design available for RAG")

        # --------------------------------------------------
        # RESET STORE IF NEEDED
        # --------------------------------------------------
        _reset_store_if_needed(state)

        # --------------------------------------------------
        # SKIP IF ALREADY INGESTED
        # --------------------------------------------------
        if not _should_ingest(state):
            state.log("RAG already ingested → skipping")
            return

        # --------------------------------------------------
        # CONVERT DESIGN → DOCS
        # --------------------------------------------------
        docs = design_to_docs(design)

        # --------------------------------------------------
        # INGEST INTO STORE
        # --------------------------------------------------
        STORE.add_many(docs)

        # --------------------------------------------------
        # BUILD CONTEXT SUMMARY
        # --------------------------------------------------
        summary = _build_context_summary(docs)

        # --------------------------------------------------
        # UPDATE STATE
        # --------------------------------------------------
        state["rag_docs"] = docs
        state["rag_context"] = STORE.data
        state["rag_summary"] = summary
        state["rag_ingested"] = True

        # Snapshot
        state.snapshot("rag")

        # --------------------------------------------------
        # LOGGING
        # --------------------------------------------------
        state.log(f"RAG ingestion complete: {len(docs)} documents")
        state.log(f"RAG summary: {summary}")

    except Exception as e:
        state.add_error(f"RAG failed: {str(e)}")
        state.log("RAG error occurred", level="ERROR")
      
