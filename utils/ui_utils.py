# app/utils.py

import json
import os
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

import streamlit as st

# --------------------------------------------------
# PATH CONFIG
# --------------------------------------------------
BASE_DIR = Path("data")
UPLOAD_DIR = BASE_DIR / "uploads"
PROCESSED_DIR = BASE_DIR / "processed"

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# SESSION STATE HELPERS
# --------------------------------------------------
def set_design(design: Dict[str, Any]):
    """Store design in Streamlit session"""
    st.session_state["design"] = design


def get_design() -> Optional[Dict[str, Any]]:
    """Retrieve design from session"""
    return st.session_state.get("design")


def clear_design():
    """Clear current design"""
    if "design" in st.session_state:
        del st.session_state["design"]


# --------------------------------------------------
# FILE UTILITIES
# --------------------------------------------------
'''
def save_uploaded_file(uploaded_file) -> Path:
    """
    Save uploaded file to disk
    """
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}_{uploaded_file.name}"

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return file_path

'''
def save_design(design: Dict[str, Any], filename: str = None) -> Path:
    """
    Save processed design JSON
    """
    if not filename:
        filename = f"design_{uuid.uuid4().hex}.json"

    file_path = PROCESSED_DIR / filename

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(design, f, indent=2)

    return file_path


def load_design(file_path: Path) -> Dict[str, Any]:
    """
    Load design JSON
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------
# VALIDATION UTILITIES
# --------------------------------------------------
def is_valid_design(design: Dict[str, Any]) -> bool:
    """
    Basic validation
    """
    if not isinstance(design, dict):
        return False

    if "components" not in design or "nets" not in design:
        return False

    return True


def get_design_summary(design: Dict[str, Any]) -> Dict[str, int]:
    """
    Quick stats for UI
    """
    return {
        "components": len(design.get("components", [])),
        "nets": len(design.get("nets", [])),
        "routes": len(design.get("routes", [])),
        "placed": len(design.get("layout", {}))
    }


# --------------------------------------------------
# DISPLAY HELPERS
# --------------------------------------------------
def show_success(message: str):
    st.success(f"✅ {message}")


def show_error(message: str):
    st.error(f"❌ {message}")


def show_info(message: str):
    st.info(f"ℹ️ {message}")


# --------------------------------------------------
# JSON DOWNLOAD
# --------------------------------------------------
def download_design_button(design: Dict[str, Any], filename="pcb_design.json"):
    """
    Streamlit download button
    """
    st.download_button(
        label="📥 Download Design",
        data=json.dumps(design, indent=2),
        file_name=filename,
        mime="application/json"
    )


# --------------------------------------------------
# TEMP FILE HANDLING
# --------------------------------------------------
def create_temp_file(content: bytes, suffix=".json") -> Path:
    """
    Create temporary file
    """
    file_path = UPLOAD_DIR / f"temp_{uuid.uuid4().hex}{suffix}"

    with open(file_path, "wb") as f:
        f.write(content)

    return file_path


# --------------------------------------------------
# CLEANUP
# --------------------------------------------------
def cleanup_temp_files():
    """
    Remove temp files (optional maintenance)
    """
    for f in UPLOAD_DIR.glob("temp_*"):
        try:
            f.unlink()
        except:
            pass


# --------------------------------------------------
# DEBUG
# --------------------------------------------------
if __name__ == "__main__":
    sample = {
        "components": [{"ref": "R1"}],
        "nets": []
    }

    path = save_design(sample)
    print("Saved:", path)

    loaded = load_design(path)
    print("Loaded:", loaded)
