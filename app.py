# app/app.py

import streamlit as st

# --------------------------------------------------
# APP CONFIG
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
# HEADER
# --------------------------------------------------
def render_header():
    col1, col2 = st.columns([8, 2])

    with col1:
        st.title("🤖 PCB AI Copilot")
        st.caption("End-to-End AI Powered PCB Design System")

    with col2:
        if st.button("🧹 Reset App"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


render_header()

# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------
def render_sidebar():
    st.sidebar.title("📂 Navigation")

    page = st.sidebar.radio(
        "Go to",
        ["Upload", "Chat", "Visualize", "Download"]
    )

    st.sidebar.markdown("---")

    # Quick status
    if st.session_state.get("design"):
        st.sidebar.success("✅ Design Loaded")
    else:
        st.sidebar.warning("⚠️ No Design")

    st.sidebar.markdown("---")
    st.sidebar.caption("🚀 AI PCB Engine")

    return page


page = render_sidebar()

# --------------------------------------------------
# PAGE ROUTING
# --------------------------------------------------
def load_page(page_name: str):
    if page_name == "Upload":
        from app.pages import upload as page_module
    elif page_name == "Chat":
        from app.pages import chat as page_module
    elif page_name == "Visualize":
        from app.pages import visualize as page_module
    elif page_name == "Download":
        from app.pages import download as page_module
    else:
        st.error("Unknown page")
        return

    page_module.run()


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
