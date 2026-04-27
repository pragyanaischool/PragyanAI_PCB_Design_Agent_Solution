# utils/json_utils.py

import json
from pathlib import Path
from typing import Any


def read_json(file_path: Path) -> Any:
    """Read JSON file safely"""
    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} not found")

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(data: Any, file_path: Path, indent: int = 2):
    """Write JSON safely"""
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent)


def pretty_json(data: Any) -> str:
    """Return formatted JSON string"""
    return json.dumps(data, indent=2)


def validate_json(data: Any, required_keys: list) -> bool:
    """Basic validation"""
    if not isinstance(data, dict):
        return False

    for key in required_keys:
        if key not in data:
            return False

    return True
