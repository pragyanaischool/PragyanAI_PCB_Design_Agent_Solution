# app/components/chat_panel.py

import streamlit as st
from typing import List, Dict, Any

# Optional: Groq LLM
try:
    from groq import Groq
    import os
    GROQ_ENABLED = True
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
except Exception:
    GROQ_ENABLED = False
    client = None


# --------------------------------------------------
# SESSION INIT
# --------------------------------------------------
def init_chat():
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []


def get_chat_history() -> List[Dict[str, str]]:
    return st.session_state.get("chat_history", [])


def add_message(role: str, content: str):
    st.session_state["chat_history"].append({
        "role": role,
        "content": content
    })


def clear_chat():
    st.session_state["chat_history"] = []


# --------------------------------------------------
# PROMPT BUILDER
# --------------------------------------------------
def build_prompt(query: str, design: Dict[str, Any], context_docs: List[Dict]):
    """
    Build structured prompt for LLM
    """

    design_summary = f"""
Components: {len(design.get("components", []))}
Nets: {len(design.get("nets", []))}
Routes: {len(design.get("routes", []))}
"""

    context = "\n".join([d["text"] for d in context_docs])

    return f"""
You are an expert PCB design assistant.

Design Summary:
{design_summary}

Context:
{context}

User Question:
{query}

Give a clear, engineering-focused answer.
"""


# --------------------------------------------------
# SIMPLE RAG RETRIEVAL
# --------------------------------------------------
def simple_retrieve(query: str, store):
    if not store:
        return []

    return [
        d for d in store.data
        if query.lower() in d["text"].lower()
    ]


# --------------------------------------------------
# LLM RESPONSE
# --------------------------------------------------
def generate_response(prompt: str) -> str:
    if GROQ_ENABLED:
        try:
            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"LLM Error: {e}"

    # Fallback (no LLM)
    return "⚠️ LLM not enabled. Showing fallback response.\n\n" + prompt[:300]


# --------------------------------------------------
# CHAT UI
# --------------------------------------------------
def render_chat(design=None, rag_store=None):
    init_chat()

    st.subheader("💬 PCB AI Chat")

    # Display chat history
    for msg in get_chat_history():
        if msg["role"] == "user":
            st.markdown(f"**🧑 You:** {msg['content']}")
        else:
            st.markdown(f"**🤖 AI:** {msg['content']}")

    # Input box
    user_input = st.chat_input("Ask about your PCB design...")

    if user_input:
        add_message("user", user_input)

        # Retrieve context
        context_docs = simple_retrieve(user_input, rag_store)

        # Build prompt
        prompt = build_prompt(user_input, design or {}, context_docs)

        # Generate response
        response = generate_response(prompt)

        add_message("assistant", response)

        st.rerun()

    # Controls
    col1, col2 = st.columns(2)

    if col1.button("🧹 Clear Chat"):
        clear_chat()
        st.rerun()

    if col2.button("📊 Show Context"):
        st.write("### Debug Context")
        if rag_store:
            st.json(rag_store.data)
        else:
            st.info("No RAG store available")
          
