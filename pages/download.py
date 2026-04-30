# app/pages/4_download.py

import streamlit as st
import json
from datetime import datetime
from pathlib import Path

from utils import (
    get_design,
    save_design,
    download_design_button,
    show_success,
    show_info
)

# --------------------------------------------------
# EXPORT HELPERS
# --------------------------------------------------
def _export_json(design):
    return json.dumps(design, indent=2)


def _export_bom(design):
    """
    Generate simple BOM CSV
    """
    lines = ["ref,value,footprint"]

    for c in design.get("components", []):
        ref = c.get("ref", "")
        val = c.get("value", "")
        fp = c.get("footprint", "")
        lines.append(f"{ref},{val},{fp}")

    return "\n".join(lines)


def _export_kicad_stub(design):
    """
    Stub for KiCad export
    """
    return f"(kicad_pcb (components {len(design.get('components', []))}))"


def _export_gerber_stub(design):
    """
    Stub for Gerber export
    """
    return "G04 Gerber placeholder*\nM02*"


# --------------------------------------------------
# PREVIEW PANEL
# --------------------------------------------------
def _preview(design):
    st.subheader("📄 Design Preview")

    with st.expander("View JSON"):
        st.json(design)


# --------------------------------------------------
# EXPORT OPTIONS
# --------------------------------------------------
def _export_options(design):
    st.subheader("📦 Export Options")

    col1, col2 = st.columns(2)

    # JSON
    with col1:
        st.write("### 📄 JSON")
        json_data = _export_json(design)
        st.download_button(
            "Download JSON",
            data=json_data,
            file_name="pcb_design.json",
            mime="application/json"
        )

    # BOM
    with col2:
        st.write("### 📋 BOM")
        bom_data = _export_bom(design)
        st.download_button(
            "Download BOM (CSV)",
            data=bom_data,
            file_name="bom.csv",
            mime="text/csv"
        )

    st.divider()

    col3, col4 = st.columns(2)

    # KiCad
    with col3:
        st.write("### 🛠 KiCad")
        kicad_data = _export_kicad_stub(design)
        st.download_button(
            "Download KiCad PCB",
            data=kicad_data,
            file_name="board.kicad_pcb",
            mime="text/plain"
        )

    # Gerber
    with col4:
        st.write("### 🏭 Gerber")
        gerber_data = _export_gerber_stub(design)
        st.download_button(
            "Download Gerber",
            data=gerber_data,
            file_name="gerber.gbr",
            mime="text/plain"
        )


# --------------------------------------------------
# SAVE TO SERVER
# --------------------------------------------------
def _save_server(design):
    st.subheader("💾 Save to Server")

    filename = f"pcb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    if st.button("Save Design"):
        path = save_design(design, filename)
        show_success(f"Saved at: {path}")


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------
def _summary(design):
    st.subheader("📊 Summary")

    col1, col2, col3 = st.columns(3)

    col1.metric("Components", len(design.get("components", [])))
    col2.metric("Nets", len(design.get("nets", [])))
    col3.metric("Routes", len(design.get("routes", [])))


# --------------------------------------------------
# MAIN PAGE
# --------------------------------------------------
def run():
    st.header("📥 Download & Export PCB")

    design = get_design()

    # --------------------------------------------------
    # NO DESIGN
    # --------------------------------------------------
    if not design:
        show_info("⚠️ No design available. Upload and process first.")
        return

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------
    _summary(design)

    st.divider()

    # --------------------------------------------------
    # PREVIEW
    # --------------------------------------------------
    _preview(design)

    st.divider()

    # --------------------------------------------------
    # EXPORT OPTIONS
    # --------------------------------------------------
    _export_options(design)

    st.divider()

    # --------------------------------------------------
    # SAVE
    # --------------------------------------------------
    _save_server(design)
  
