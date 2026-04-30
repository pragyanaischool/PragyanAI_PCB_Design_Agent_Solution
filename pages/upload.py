# app/pages/1_upload.py

import streamlit as st
import time

from app.components.uploader import uploader
from app.core.pipeline import run_pipeline
from app.utils import (
    set_design,
    get_design,
    show_success,
    show_error,
    show_info,
    get_design_summary,
    save_design
)


# --------------------------------------------------
# UI HEADER
# --------------------------------------------------
def _header():
    st.header("📤 Upload & Process PCB Design")
    st.caption("Upload JSON / CSV / KiCad / Altium → Auto Design Pipeline")


# --------------------------------------------------
# PROCESSING WITH PROGRESS
# --------------------------------------------------
def _run_pipeline_with_ui(file_data):
    progress = st.progress(0)
    status = st.empty()

    try:
        status.info("📥 Reading input...")
        progress.progress(10)

        time.sleep(0.2)

        status.info("🔍 Parsing & normalization...")
        progress.progress(30)

        time.sleep(0.2)

        status.info("🧠 Enrichment (pins + footprints)...")
        progress.progress(50)

        time.sleep(0.2)

        status.info("📐 Layout + Routing...")
        progress.progress(70)

        time.sleep(0.2)

        # --------------------------------------------------
        # ACTUAL PIPELINE CALL
        # --------------------------------------------------
        if file_data["type"] == "csv_netlist":
            design = run_pipeline({
                "components": str(file_data["components"]),
                "nets": str(file_data["nets"])
            })
        else:
            design = run_pipeline(str(file_data["path"]))

        progress.progress(100)
        status.success("✅ Processing complete")

        return design

    except Exception as e:
        progress.empty()
        status.error("❌ Processing failed")
        raise e


# --------------------------------------------------
# DESIGN PREVIEW
# --------------------------------------------------
def _preview_design(design):
    st.subheader("📄 Design Preview")

    summary = get_design_summary(design)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Components", summary["components"])
    col2.metric("Nets", summary["nets"])
    col3.metric("Routes", summary["routes"])
    col4.metric("Placed", summary["placed"])

    with st.expander("🔍 View Full JSON"):
        st.json(design)


# --------------------------------------------------
# MAIN PAGE
# --------------------------------------------------
def run():
    _header()

    # Upload UI
    file_data = uploader()

    if not file_data:
        show_info("Upload a file to begin")
        return

    # Process button
    if st.button("🚀 Run PCB Pipeline", use_container_width=True):
        try:
            design = _run_pipeline_with_ui(file_data)

            # Store in session
            set_design(design)

            show_success("Design successfully generated!")

            # Preview
            _preview_design(design)

        except Exception as e:
            show_error(f"Error: {e}")
            return

    # --------------------------------------------------
    # EXISTING DESIGN (SESSION)
    # --------------------------------------------------
    existing_design = get_design()

    if existing_design:
        st.divider()
        st.subheader("📦 Current Loaded Design")

        _preview_design(existing_design)

        # Save option
        if st.button("💾 Save Design"):
            path = save_design(existing_design)
            show_success(f"Saved at: {path}")

        # Reset option
        if st.button("🧹 Clear Design"):
            st.session_state.pop("design", None)
            st.rerun()
          
