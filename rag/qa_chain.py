# rag/qa_chain.py

from typing import Dict, Any, List, Optional

# RAG Components
from rag.retriever import retrieve, build_context
from rag.prompts import (
    build_qa_prompt,
    build_chat_prompt
)
from rag.memory import ChatMemory
from rag.vector_store import VectorStore
from rag.refine import refine_answer

# Optional LLM (Groq)
import os

try:
    from groq import Groq
    GROQ_ENABLED = True
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
except Exception:
    GROQ_ENABLED = False
    client = None


# ==================================================
# LLM CALL
# ==================================================
def _call_llm(prompt: str) -> str:
    """
    Calls Groq LLM if available, else fallback
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

    # Fallback mode
    return f"""
⚠️ LLM not enabled.

Generated Prompt (preview):
{prompt[:500]}
"""


# ==================================================
# BASIC QA (NO MEMORY)
# ==================================================
def run_qa(
    query: str,
    design: Dict[str, Any],
    store: VectorStore,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Simple RAG pipeline
    """

    # Step 1: Retrieve
    docs = retrieve(query, store, top_k=top_k)

    # Step 2: Build prompt
    prompt = build_qa_prompt(query, design, docs)

    # Step 3: LLM
    answer = _call_llm(prompt)

    # Step 4: Optional refinement
    answer = refine_answer(answer, docs)

    return {
        "query": query,
        "answer": answer,
        "context": docs,
        "prompt": prompt
    }


# ==================================================
# CHAT WITH MEMORY
# ==================================================
def run_chat(
    query: str,
    design: Dict[str, Any],
    store: VectorStore,
    memory: ChatMemory,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    RAG + memory-enabled chat
    """

    # Step 1: Retrieve context
    docs = retrieve(query, store, top_k=top_k)

    # Step 2: Build prompt with memory
    prompt = build_chat_prompt(
        query=query,
        design=design,
        docs=docs,
        history=memory.get_recent()
    )

    # Step 3: LLM call
    answer = _call_llm(prompt)

    # Step 4: Update memory
    memory.add("user", query)
    memory.add("assistant", answer)

    return {
        "answer": answer,
        "context": docs,
        "prompt": prompt,
        "memory_size": len(memory)
    }


# ==================================================
# ADVANCED QA (STRUCTURED OUTPUT)
# ==================================================
def run_structured_qa(
    query: str,
    design: Dict[str, Any],
    store: VectorStore,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Structured AI response (useful for agents)
    """

    docs = retrieve(query, store, top_k=top_k)

    context = build_context(docs)

    prompt = f"""
You are a PCB AI system.

Context:
{context}

User Request:
{query}

Return JSON:
{{
  "analysis": "...",
  "recommendations": ["..."],
  "actions": ["..."]
}}
"""

    answer = _call_llm(prompt)

    return {
        "raw_response": answer,
        "context": docs,
        "prompt": prompt
    }


# ==================================================
# DEBUG / TEST
# ==================================================
if __name__ == "__main__":
    from rag.vector_store import VectorStore
    from rag.memory import ChatMemory

    store = VectorStore()
    memory = ChatMemory()

    # Sample data
    store.add("R1 is a 10k resistor", {"type": "component"})
    store.add("C1 is a capacitor", {"type": "component"})

    design = {
        "components": [{"ref": "R1", "value": "10k"}],
        "nets": []
    }

    print("\n--- QA ---")
    result = run_qa("What is R1?", design, store)
    print(result["answer"])

    print("\n--- CHAT ---")
    chat = run_chat("Explain resistor role", design, store, memory)
    print(chat["answer"])
  
