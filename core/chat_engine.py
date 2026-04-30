# app/core/chat_engine.py

from typing import List, Dict, Any
import os

# --------------------------------------------------
# RAG COMPONENTS
# --------------------------------------------------
from scripts.ingest_rag import design_to_docs, SimpleVectorStore

# Global vector store (in-memory)
store = SimpleVectorStore()


# --------------------------------------------------
# OPTIONAL LLM (GROQ)
# --------------------------------------------------
try:
    from groq import Groq
    GROQ_ENABLED = True
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
except Exception:
    GROQ_ENABLED = False
    client = None


# --------------------------------------------------
# INGEST DESIGN INTO RAG
# --------------------------------------------------
def ingest_design(design: Dict[str, Any]) -> int:
    """
    Convert design → documents → vector store
    Returns number of docs ingested
    """
    docs = design_to_docs(design)

    for d in docs:
        store.add(d["text"], d["metadata"])

    return len(docs)


# --------------------------------------------------
# RETRIEVAL (SIMPLE / KEYWORD)
# --------------------------------------------------
def retrieve(query: str, top_k: int = 5) -> List[Dict]:
    """
    Basic retrieval (can upgrade to embeddings later)
    """
    query = query.lower()

    results = [
        d for d in store.data
        if query in d["text"].lower()
    ]

    return results[:top_k]


# --------------------------------------------------
# BUILD PROMPT
# --------------------------------------------------
def build_prompt(
    query: str,
    design: Dict[str, Any],
    context_docs: List[Dict]
) -> str:
    """
    Construct structured prompt for LLM
    """

    # Design summary
    summary = f"""
Components: {len(design.get("components", []))}
Nets: {len(design.get("nets", []))}
Routes: {len(design.get("routes", []))}
"""

    # Context
    context = "\n".join([d["text"] for d in context_docs])

    return f"""
You are an expert PCB design assistant.

Design Summary:
{summary}

Context:
{context}

User Question:
{query}

Give a precise, engineering-focused answer.
"""


# --------------------------------------------------
# LLM CALL
# --------------------------------------------------
def call_llm(prompt: str) -> str:
    """
    Call Groq LLM if available, else fallback
    """

    if GROQ_ENABLED and client:
        try:
            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            return response.choices[0].message.content

        except Exception as e:
            return f"⚠️ LLM Error: {e}"

    # Fallback (no LLM)
    return f"""
⚠️ LLM not enabled.

Generated prompt (preview):
{prompt[:500]}
"""


# --------------------------------------------------
# MAIN CHAT FUNCTION
# --------------------------------------------------
def chat(
    query: str,
    design: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Full RAG + LLM pipeline
    """

    # Step 1: Retrieve context
    context_docs = retrieve(query)

    # Step 2: Build prompt
    prompt = build_prompt(query, design, context_docs)

    # Step 3: Generate response
    answer = call_llm(prompt)

    return {
        "query": query,
        "answer": answer,
        "context_used": context_docs,
        "prompt": prompt  # useful for debugging
    }


# --------------------------------------------------
# CHAT WITH HISTORY
# --------------------------------------------------
def chat_with_history(
    query: str,
    design: Dict[str, Any],
    history: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Chat with conversational memory
    """

    # Include previous conversation
    history_text = "\n".join([
        f"{msg['role']}: {msg['content']}"
        for msg in history[-5:]  # last 5 messages
    ])

    context_docs = retrieve(query)

    prompt = f"""
You are an expert PCB design assistant.

Conversation History:
{history_text}

Context:
{chr(10).join([d["text"] for d in context_docs])}

User Question:
{query}

Provide a helpful, context-aware answer.
"""

    answer = call_llm(prompt)

    return {
        "answer": answer,
        "context_used": context_docs
    }


# --------------------------------------------------
# CLEAR STORE
# --------------------------------------------------
def reset_store():
    global store
    store = SimpleVectorStore()


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample_design = {
        "components": [{"ref": "R1", "value": "10k"}],
        "nets": [{"name": "SIG", "connections": ["R1:1"]}]
    }

    ingest_design(sample_design)

    response = chat("What is R1?", sample_design)

    print(response["answer"])
  
