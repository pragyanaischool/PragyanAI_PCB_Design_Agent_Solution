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
# HEADER (HARDENED)
# --------------------------------------------------
def render_header():
    if st.session_state.get("_header_rendered", False):
        return
    st.session_state["_header_rendered"] = True

    col1, col2 = st.columns([8, 2])

    with col1:
        st.title("🤖 PCB AI Copilot")
        st.caption("End-to-End AI Powered PCB Design System")

    with col2:
        if st.button("🧹 Reset App", key="reset_app_btn"):
            keys_to_keep = {"_header_rendered", "_sidebar_rendered"}

            for key in list(st.session_state.keys()):
                if key not in keys_to_keep:
                    del st.session_state[key]

            st.rerun()

# Render header once per run
render_header()

# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------
def render_sidebar():
    # 🔥 Prevent duplicate sidebar rendering
    if st.session_state.get("_sidebar_rendered", False):
        return st.session_state.get("_selected_page", "Upload")

    st.session_state["_sidebar_rendered"] = True

    st.sidebar.title("📂 Navigation")

    page = st.sidebar.radio(
        "Go to",
        ["Upload", "Chat", "Visualize", "Download"],
        key="nav_radio_unique"   # 🔥 also change key
    )

    # Store selected page safely
    st.session_state["_selected_page"] = page

    st.sidebar.markdown("---")

    if st.session_state.get("design"):
        st.sidebar.success("✅ Design Loaded")
    else:
        st.sidebar.warning("⚠️ No Design")

    st.sidebar.markdown("---")
    st.sidebar.caption("🚀 AI PCB Engine")

    return page

# --------------------------------------------------
# PAGE ROUTING (SAFE IMPORT)
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
        module = importlib.import_module(f"pages.{module_name}")

        # 🔥 Ensure each page exposes run()
        if hasattr(module, "run"):
            module.run()
        else:
            st.error(f"{module_name}.py must define run()")

    except Exception as e:
        st.error(f"Error loading page: {e}")

page = render_sidebar()  # 2️⃣ sidebar renders ← HERE
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
