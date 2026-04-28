# enrichment/pin_mapping.py

import json
from pathlib import Path
from typing import List, Dict, Any

from utils.logger import get_module_logger

logger = get_module_logger(__name__)

# --------------------------------------------------
# LOAD PIN DATABASE
# --------------------------------------------------
DB_PATH = Path(__file__).parent / "db" / "symbol_pins.json"


def load_pin_db() -> Dict[str, Any]:
    if not DB_PATH.exists():
        logger.warning("Pin DB not found, using empty DB")
        return {}

    try:
        with open(DB_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load pin DB: {e}")
        return {}


PIN_DB = load_pin_db()


# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def normalize_key(value: str) -> str:
    return str(value or "").strip().upper()


def normalize_pins(pins):
    if isinstance(pins, str):
        return [p.strip().upper() for p in pins.split(",") if p.strip()]
    if isinstance(pins, list):
        return [str(p).strip().upper() for p in pins]
    return []


def match_symbol(value: str) -> str:
    """
    Try to match component value to DB key
    """
    val = normalize_key(value)

    # Direct match
    if val in PIN_DB:
        return val

    # Partial match (e.g., ATMEGA328P → ATMEGA328)
    for key in PIN_DB:
        if key in val:
            return key

    return ""


# --------------------------------------------------
# FALLBACK PIN INFERENCE
# --------------------------------------------------
def infer_pins(value: str) -> List[str]:
    """
    Basic heuristic pin generation
    """
    val = normalize_key(value)

    if "RES" in val or "K" in val:
        return ["1", "2"]

    if "CAP" in val or "F" in val:
        return ["1", "2"]

    if "DIODE" in val:
        return ["A", "K"]

    if "TRANSISTOR" in val or "MOSFET" in val:
        return ["G", "D", "S"]

    return []


# --------------------------------------------------
# MAIN PIN MAPPING FUNCTION
# --------------------------------------------------
def map_pins(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Add or normalize pins for each component
    """

    logger.info("Starting pin mapping")

    for comp in components:
        try:
            value = comp.get("value", "")
            ref = comp.get("ref", "")

            # Normalize existing pins
            existing_pins = normalize_pins(comp.get("pins", []))

            # If pins already exist → normalize only
            if existing_pins:
                comp["pins"] = existing_pins
                continue

            # Try DB lookup
            match = match_symbol(value)

            if match:
                comp["pins"] = normalize_pins(PIN_DB[match])
                logger.debug(f"Mapped pins for {ref} using DB ({match})")
                continue

            # Fallback inference
            inferred = infer_pins(value)

            if inferred:
                comp["pins"] = inferred
                logger.debug(f"Inferred pins for {ref}")
            else:
                comp["pins"] = []
                logger.warning(f"No pin mapping for {ref} ({value})")

        except Exception as e:
            logger.warning(f"Pin mapping failed for {comp}: {e}")
            comp["pins"] = []

    logger.info("Pin mapping completed")

    return components


# --------------------------------------------------
# OPTIONAL: PIN NUMBER MAPPING
# --------------------------------------------------
def map_pin_numbers(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Assign numeric pin indices if missing
    """

    for comp in components:
        pins = comp.get("pins", [])

        comp["pin_map"] = {
            pin: str(i + 1) for i, pin in enumerate(pins)
        }

    return components


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample = [
        {"ref": "U1", "value": "ATmega328P"},
        {"ref": "R1", "value": "10k"},
        {"ref": "Q1", "value": "MOSFET"},
        {"ref": "C1", "value": "100nF"},
    ]

    result = map_pins(sample)

    for c in result:
        print(c)
      
