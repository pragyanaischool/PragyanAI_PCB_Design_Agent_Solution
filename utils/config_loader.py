# utils/config_loader.py

import json
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def load_json_config(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml_config(path: Path):
    if yaml is None:
        raise ImportError("PyYAML not installed")

    if not path.exists():
        raise FileNotFoundError(f"{path} not found")

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_config(path: Path):
    """Auto-detect config type"""
    if path.suffix == ".json":
        return load_json_config(path)
    elif path.suffix in [".yaml", ".yml"]:
        return load_yaml_config(path)
    else:
        raise ValueError("Unsupported config format")
      
