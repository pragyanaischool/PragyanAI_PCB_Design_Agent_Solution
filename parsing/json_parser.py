# parsing/json_parser.py

import json
from pathlib import Path
from typing import Dict, Any, List

from utils.logger import get_module_logger

logger = get_module_logger(__name__)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def safe_list(value):
    """Ensure value is always a list"""
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    return []


def normalize_component(comp: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize component structure
    """
    return {
        "ref": str(comp.get("ref", "")).strip(),
        "value": str(comp.get("value", "")).strip(),
        "footprint": str(comp.get("footprint", "")).strip(),
        "pins": safe_list(comp.get("pins", []))
    }


def normalize_net(net: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize net structure
    """
    name = net.get("name") or net.get("net") or "UNKNOWN"

    return {
        "name": str(name).strip(),
        "connections": safe_list(net.get("connections", []))
    }


def validate_component(comp: Dict[str, Any]) -> bool:
    return bool(comp.get("ref"))


def validate_net(net: Dict[str, Any]) -> bool:
    return bool(net.get("name"))


# --------------------------------------------------
# PARSE JSON FILE
# --------------------------------------------------
def load_json(file_path: Path) -> Dict[str, Any]:
    """
    Load JSON safely
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to read JSON file: {e}")
        raise


# --------------------------------------------------
# MAIN PARSER
# --------------------------------------------------
def parse_json(file_path: Path) -> Dict[str, Any]:
    """
    Parse JSON into unified design format

    Supports:
    - Standard format
    - Slight variations (net vs name, etc.)
    """

    logger.info(f"Parsing JSON file: {file_path}")

    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} not found")

    data = load_json(file_path)

    raw_components = data.get("components", [])
    raw_nets = data.get("nets", [])

    components: List[Dict[str, Any]] = []
    nets: List[Dict[str, Any]] = []

    # -----------------------------
    # COMPONENTS
    # -----------------------------
    for i, comp in enumerate(raw_components, start=1):
        try:
            c = normalize_component(comp)

            if not validate_component(c):
                logger.warning(f"Skipping invalid component at index {i}")
                continue

            components.append(c)

        except Exception as e:
            logger.warning(f"Component parsing failed at {i}: {e}")

    # -----------------------------
    # NETS
    # -----------------------------
    for i, net in enumerate(raw_nets, start=1):
        try:
            n = normalize_net(net)

            if not validate_net(n):
                logger.warning(f"Skipping invalid net at index {i}")
                continue

            nets.append(n)

        except Exception as e:
            logger.warning(f"Net parsing failed at {i}: {e}")

    design = {
        "components": components,
        "nets": nets
    }

    logger.info(
        f"JSON parsed successfully: "
        f"{len(components)} components, {len(nets)} nets"
    )

    return design


# --------------------------------------------------
# OPTIONAL: SCHEMA VALIDATION
# --------------------------------------------------
def validate_design(design: Dict[str, Any]) -> bool:
    """
    Basic schema validation
    """

    if "components" not in design or "nets" not in design:
        return False

    for comp in design["components"]:
        if not comp.get("ref"):
            return False

    for net in design["nets"]:
        if not net.get("name"):
            return False

    return True


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    test_file = Path("input.json")

    if test_file.exists():
        design = parse_json(test_file)

        print("\nComponents:")
        for c in design["components"]:
            print(c)

        print("\nNets:")
        for n in design["nets"]:
            print(n)
    else:
        print("Test JSON file not found")
      
