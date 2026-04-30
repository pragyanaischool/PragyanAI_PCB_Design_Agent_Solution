# app/pages/3_visualize.py

import streamlit as st

from components.pcb_viewer import interactive_view, show_pcb
from utils import get_design, show_info


# --------------------------------------------------
# HEADER
# --------------------------------------------------
def _header():
    st.header("📊 PCB Visualization")
    st.caption("Explore layout, routing, and connectivity")


# --------------------------------------------------
# DESIGN STATS
# --------------------------------------------------
def _design_stats(design):
    st.subheader("📈 Design Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Components", len(design.get("components", [])))
    col2.metric("Nets", len(design.get("nets", [])))
    col3.metric("Routes", len(design.get("routes", [])))
    col4.metric("Placed", len(design.get("layout", {})))


# --------------------------------------------------
# COMPONENT INSPECTOR
# --------------------------------------------------
def _component_inspector(design):
    st.subheader("🔧 Component Inspector")

    components = design.get("components", [])

    if not components:
        st.info("No components found")
        return

    refs = [c.get("ref") for c in components]

    selected = st.selectbox("Select Component", refs)

    comp = next((c for c in components if c["ref"] == selected), None)

    if comp:
        st.json(comp)


# --------------------------------------------------
# NET INSPECTOR
# --------------------------------------------------
def _net_inspector(design):
    st.subheader("🔌 Net Inspector")

    nets = design.get("nets", [])

    if not nets:
        st.info("No nets found")
        return

    names = [n.get("name") for n in nets]

    selected = st.selectbox("Select Net", names)

    net = next((n for n in nets if n["name"] == selected), None)

    if net:
        st.write("### Connections")
        for conn in net.get("connections", []):
            st.write("-", conn)


# --------------------------------------------------
# DEBUG PANEL
# --------------------------------------------------
def _debug_panel(design):
    with st.expander("🛠 Debug View"):
        st.write("### Raw Design JSON")
        st.json(design)


# --------------------------------------------------
# MAIN PAGE
# --------------------------------------------------
def run():
    _header()

    design = get_design()

    # --------------------------------------------------
    # NO DESIGN
    # --------------------------------------------------
    if not design:
        show_info("⚠️ No design available. Please upload first.")
        return

    # --------------------------------------------------
    # OVERVIEW
    # --------------------------------------------------
    _design_stats(design)

    st.divider()

    # --------------------------------------------------
    # VIEW MODE SELECTOR
    # --------------------------------------------------
    mode = st.radio(
        "Select View Mode",
        ["Interactive View", "Full Layout", "Inspect"],
        horizontal=True
    )

    # --------------------------------------------------
    # INTERACTIVE VIEW
    # --------------------------------------------------
    if mode == "Interactive View":
        interactive_view(design)

    # --------------------------------------------------
    # STATIC FULL VIEW
    # --------------------------------------------------
    elif mode == "Full Layout":
        show_pcb(design)

    # --------------------------------------------------
    # INSPECT MODE
    # --------------------------------------------------
    elif mode == "Inspect":
        col1, col2 = st.columns(2)

        with col1:
            _component_inspector(design)

        with col2:
            _net_inspector(design)

    st.divider()

    # --------------------------------------------------
    # DEBUG
    # --------------------------------------------------
    _debug_panel(design)
  
