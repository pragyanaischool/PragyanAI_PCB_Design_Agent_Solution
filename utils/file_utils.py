# utils/file_utils.py

import os
from pathlib import Path
from typing import List
from config.settings import settings


def ensure_dir(path: Path):
    """Ensure directory exists"""
    path.mkdir(parents=True, exist_ok=True)


def get_file_extension(file_path: str) -> str:
    return Path(file_path).suffix.lower()


def is_supported_file(file_path: str, allowed_ext: List[str]) -> bool:
    return get_file_extension(file_path) in allowed_ext


def save_uploaded_file(uploaded_file, save_dir: Path) -> Path:
    """Save Streamlit uploaded file"""
    ensure_dir(save_dir)

    file_path = save_dir / uploaded_file.name

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return file_path


def list_files(directory: Path, extension: str = None) -> List[Path]:
    """List files optionally filtered by extension"""
    if not directory.exists():
        return []

    files = list(directory.glob("*"))
    if extension:
        files = [f for f in files if f.suffix == extension]

    return files


def generate_output_path(filename: str, subfolder: str = "images") -> Path:
    """Generate path inside outputs folder"""
    output_dir = settings.OUTPUT_DIR / subfolder
    ensure_dir(output_dir)
    return output_dir / filename


def delete_file(file_path: Path):
    if file_path.exists():
        file_path.unlink()


def clean_directory(directory: Path):
    """Remove all files in directory"""
    if not directory.exists():
        return

    for f in directory.iterdir():
        if f.is_file():
            f.unlink()
