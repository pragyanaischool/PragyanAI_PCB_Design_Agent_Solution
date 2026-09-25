# app/utils.py

import json
import os
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, Union

import streamlit as st

# --------------------------------------------------
# PATH CONFIG
# --------------------------------------------------
BASE_DIR = Path("data")
UPLOAD_DIR = BASE_DIR / "uploads"
PROCESSED_DIR = BASE_DIR / "processed"

# Ensure directories exist securely
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# SESSION STATE HELPERS
# --------------------------------------------------
def set_design(design: Dict[str, Any]):
    """Store design data safely in Streamlit session state."""
    if isinstance(design, dict):
        st.session_state["design"] = design
    else:
        raise ValueError("Design state must be a dictionary.")


def get_design() -> Optional[Dict[str, Any]]:
    """Retrieve design data from session state."""
    return st.session_state.get("design", None)


def clear_design():
    """Clear current design state."""
    if "design" in st.session_state:
        del st.session_state["design"]


# --------------------------------------------------
# FILE UTILITIES
# --------------------------------------------------
def save_uploaded_file(uploaded_file) -> Path:
    """Save an uploaded file safely to disk with a unique identifier."""
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}_{uploaded_file.name}"

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return file_path


def save_design(design: Dict[str, Any], filename: Optional[str] = None) -> Path:
    """Save processed design dictionary to a persistent JSON file."""
    if not filename:
        filename = f"design_{uuid.uuid4().hex}.json"

    file_path = PROCESSED_DIR / filename

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(design, f, indent=2)

    return file_path


def load_design(file_path: Path) -> Dict[str, Any]:
    """Load and parse design JSON from disk."""
    if not file_path.exists():
        raise FileNotFoundError(f"Design file not found at: {file_path}")
        
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------
# VALIDATION UTILITIES
# --------------------------------------------------
def is_valid_design(design: Any) -> bool:
    """Perform robust schema validation on the design payload."""
    if not isinstance(design, dict):
        return False

    # Flexible validation accepting typical agentic outputs
    required_keys = ["components", "nets"]
    return all(key in design for key in required_keys)


def get_design_summary(design: Dict[str, Any]) -> Dict[str, int]:
    """Generate safe quick statistics for the UI dashboard."""
    if not isinstance(design, dict):
        return {"components": 0, "nets": 0, "routes": 0, "placed": 0}

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
# ENHANCED JSON / MARKDOWN DOWNLOAD
# --------------------------------------------------
def download_design_button(design_data: Union[Dict[str, Any], str], filename: str = "pcb_design.json", label: str = "📥 Download Design"):
    """
    Renders an intelligent Streamlit download button supporting both 
    JSON dictionary objects and Markdown/text report strings.
    """
    if isinstance(design_data, dict):
        data_str = json.dumps(design_data, indent=2)
        mime_type = "application/json"
        if not filename.endswith(".json"):
            filename += ".json"
    else:
        data_str = str(design_data)
        mime_type = "text/markdown"
        if not filename.endswith(".md") and not filename.endswith(".txt"):
            filename += ".md"

    st.download_button(
        label=label,
        data=data_str,
        file_name=filename,
        mime=mime_type
    )


# --------------------------------------------------
# TEMP FILE HANDLING & MAINTENANCE
# --------------------------------------------------
def create_temp_file(content: bytes, suffix: str = ".json") -> Path:
    """Create a temporary file inside the upload directory."""
    file_path = UPLOAD_DIR / f"temp_{uuid.uuid4().hex}{suffix}"

    with open(file_path, "wb") as f:
        f.write(content)

    return file_path


def cleanup_temp_files():
    """Safely remove leftover temporary files to preserve storage."""
    for f in UPLOAD_DIR.glob("temp_*"):
        try:
            f.unlink()
        except Exception:
            pass


# --------------------------------------------------
# DEBUG VERIFICATION
# --------------------------------------------------
if __name__ == "__main__":
    sample = {
        "components": [{"ref": "R1", "value": "10k"}],
        "nets": [["R1.1", "VCC"]]
    }

    path = save_design(sample)
    print("Test Save Successful:", path)

    loaded = load_design(path)
    print("Test Load Successful:", loaded)
