# app/components/uploader.py

import streamlit as st
from pathlib import Path
import json
import uuid

from utils import save_uploaded_file, show_success, show_error


# --------------------------------------------------
# SUPPORTED FORMATS
# --------------------------------------------------
SUPPORTED_EXTENSIONS = [
    ".json",
    ".csv",
    ".kicad_sch",
    ".xml"
]


# --------------------------------------------------
# FILE TYPE DETECTION
# --------------------------------------------------
def detect_file_type(file_name: str) -> str:
    suffix = Path(file_name).suffix.lower()

    if suffix == ".json":
        return "json"
    elif suffix == ".csv":
        return "csv"
    elif suffix == ".kicad_sch":
        return "kicad"
    elif suffix == ".xml":
        return "altium"
    else:
        return "unknown"


# --------------------------------------------------
# SINGLE FILE UPLOAD
# --------------------------------------------------
def upload_single_file():
    st.subheader("📤 Upload PCB File")

    file = st.file_uploader(
        "Upload JSON / CSV / KiCad / Altium file",
        type=[ext.replace(".", "") for ext in SUPPORTED_EXTENSIONS]
    )

    if file:
        file_type = detect_file_type(file.name)

        if file_type == "unknown":
            show_error("Unsupported file type")
            return None

        path = save_uploaded_file(file)

        show_success(f"Uploaded {file.name} ({file_type})")

        return {
            "type": file_type,
            "path": path
        }

    return None


# --------------------------------------------------
# MULTI FILE UPLOAD (CSV NETLIST)
# --------------------------------------------------
def upload_multi_csv():
    st.subheader("📦 Upload CSV Netlist")

    col1, col2 = st.columns(2)

    components_file = col1.file_uploader(
        "Components CSV",
        type=["csv"],
        key="components_csv"
    )

    nets_file = col2.file_uploader(
        "Nets CSV",
        type=["csv"],
        key="nets_csv"
    )

    if components_file and nets_file:
        comp_path = save_uploaded_file(components_file)
        nets_path = save_uploaded_file(nets_file)

        show_success("CSV Netlist uploaded successfully")

        return {
            "type": "csv_netlist",
            "components": comp_path,
            "nets": nets_path
        }

    return None


# --------------------------------------------------
# JSON PREVIEW
# --------------------------------------------------
def preview_json(file_path: Path):
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        st.write("### 📄 JSON Preview")
        st.json(data)

    except Exception:
        st.warning("Cannot preview file")


# --------------------------------------------------
# MAIN UPLOADER UI
# --------------------------------------------------
def uploader():
    st.title("📤 PCB Upload")

    mode = st.radio(
        "Select Upload Mode",
        ["Single File", "CSV Netlist"]
    )

    result = None

    if mode == "Single File":
        result = upload_single_file()

        if result and result["type"] == "json":
            preview_json(result["path"])

    elif mode == "CSV Netlist":
        result = upload_multi_csv()

    return result


# --------------------------------------------------
# DEBUG
# --------------------------------------------------
if __name__ == "__main__":
    print("Run inside Streamlit")
