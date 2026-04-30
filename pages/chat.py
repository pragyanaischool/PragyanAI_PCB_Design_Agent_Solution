# app/pages/2_chat.py

import streamlit as st

from app.components.chat_panel import render_chat, clear_chat
from app.core.chat_engine import ingest_design, store
from app.utils import get_design, show_info, show_error


# --------------------------------------------------
# HEADER
# --------------------------------------------------
def _header():
    st.header("💬 PCB AI Assistant")
    st.caption("Ask questions, debug design, get recommendations")


# --------------------------------------------------
# DESIGN SUMMARY
# --------------------------------------------------
def _design_summary(design):
    st.subheader("📊 Design Context")

    col1, col2, col3 = st.columns(3)

    col1.metric("Components", len(design.get("components", [])))
    col2.metric("Nets", len(design.get("nets", [])))
    col3.metric("Routes", len(design.get("routes", [])))

    with st.expander("🔍 View Components"):
        for c in design.get("components", []):
            st.write(f"{c.get('ref')} - {c.get('value', '')}")


# --------------------------------------------------
# CONTROLS
# --------------------------------------------------
def _controls():
    col1, col2 = st.columns(2)

    if col1.button("🧹 Clear Chat"):
        clear_chat()
        st.rerun()

    if col2.button("🔄 Re-ingest Design"):
        st.session_state["rag_ingested"] = False
        st.rerun()


# --------------------------------------------------
# MAIN PAGE
# --------------------------------------------------
def run():
    _header()

    design = get_design()

    # --------------------------------------------------
    # NO DESIGN CASE
    # --------------------------------------------------
    if not design:
        show_info("⚠️ Please upload and process a design first")
        return

    # --------------------------------------------------
    # SHOW DESIGN SUMMARY
    # --------------------------------------------------
    _design_summary(design)

    st.divider()

    # --------------------------------------------------
    # INGEST INTO RAG (ONCE)
    # --------------------------------------------------
    if not st.session_state.get("rag_ingested", False):
        try:
            ingest_design(design)
            st.session_state["rag_ingested"] = True
            st.success("🧠 Design context loaded into AI")
        except Exception as e:
            show_error(f"RAG ingestion failed: {e}")

    # --------------------------------------------------
    # CHAT PANEL
    # --------------------------------------------------
    render_chat(
        design=design,
        rag_store=store
    )

    st.divider()

    # --------------------------------------------------
    # CONTROLS
    # --------------------------------------------------
    _controls()
  
