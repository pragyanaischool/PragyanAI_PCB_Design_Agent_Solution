# app/app.py

import streamlit as st
import importlib

# --------------------------------------------------
# APP CONFIG (ONLY ONCE)
# --------------------------------------------------
st.set_page_config(
    page_title="PCB AI Copilot",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# SESSION INIT
# --------------------------------------------------
def init_session():
    defaults = {
        "design": None,
        "chat_history": [],
        "rag_ingested": False
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session()

# --------------------------------------------------
# HEADER (FIXED)
# --------------------------------------------------
def render_header():
    col1, col2 = st.columns([8, 2])

    with col1:
        st.title("🤖 PCB AI Copilot")
        st.caption("End-to-End AI Powered PCB Design System")

    with col2:
        # ✅ FIX: Add UNIQUE key
        if st.button("🧹 Reset App", key="reset_app_btn"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# ✅ Render ONCE
render_header()

# --------------------------------------------------
# SIDEBAR NAVIGATION (FIXED)
# --------------------------------------------------
def render_sidebar():
    st.sidebar.title("📂 Navigation")

    # ✅ FIX: add key
    page = st.sidebar.radio(
        "Go to",
        ["Upload", "Chat", "Visualize", "Download"],
        key="nav_radio"
    )

    st.sidebar.markdown("---")

    if st.session_state.get("design"):
        st.sidebar.success("✅ Design Loaded")
    else:
        st.sidebar.warning("⚠️ No Design")

    st.sidebar.markdown("---")
    st.sidebar.caption("🚀 AI PCB Engine")

    return page


page = render_sidebar()

# --------------------------------------------------
# PAGE ROUTING (CRITICAL FIX)
# --------------------------------------------------
def load_page(page_name: str):
    page_map = {
        "Upload": "upload",
        "Chat": "chat",
        "Visualize": "visualize",
        "Download": "download"
    }

    module_name = page_map.get(page_name)

    if not module_name:
        st.error("Unknown page")
        return

    try:
        # ✅ FIX: Safe dynamic import (prevents duplicate execution)
        module = importlib.import_module(f"app.pages.{module_name}")

        # Ensure run() exists
        if hasattr(module, "run"):
            module.run()
        else:
            st.error(f"{module_name}.py missing run() function")

    except Exception as e:
        st.error(f"Error loading page: {e}")


load_page(page)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
def render_footer():
    st.markdown("---")
    st.caption(
        "⚙️ Built with AI | Parsing → Enrichment → Layout → Routing → DRC → RAG"
    )


render_footer()
