# enrichment/rules_engine.py

import json
from pathlib import Path
from typing import Dict, Any, List

from utils.logger import get_module_logger

logger = get_module_logger(__name__)

# --------------------------------------------------
# LOAD RULE DB
# --------------------------------------------------
DB_PATH = Path(__file__).parent / "db" / "pcb_rules.json"


def load_rules() -> Dict[str, Any]:
    if not DB_PATH.exists():
        logger.warning("Rules DB not found, using defaults")
        return {}

    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load rules DB: {e}")
        return {}


RULE_DB = load_rules()


# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def get_default_rules() -> Dict[str, Any]:
    return RULE_DB.get("default", {})


def get_net_rules(net_name: str) -> Dict[str, Any]:
    return RULE_DB.get("nets", {}).get(net_name, {})


def get_component_rules(value: str) -> Dict[str, Any]:
    return RULE_DB.get("components", {}).get(value.lower(), {})


# --------------------------------------------------
# APPLY RULES TO DESIGN
# --------------------------------------------------
def apply_rules(design: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inject rules into design (global + net + component level)
    """

    logger.info("Applying PCB rules")

    default_rules = get_default_rules()

    # --------------------------------------------------
    # APPLY GLOBAL RULES
    # --------------------------------------------------
    design["constraints"] = default_rules.copy()

    # --------------------------------------------------
    # APPLY NET-LEVEL RULES
    # --------------------------------------------------
    for net in design.get("nets", []):
        net_name = net.get("name")

        net_rules = get_net_rules(net_name)

        if net_rules:
            net["rules"] = net_rules

    # --------------------------------------------------
    # APPLY COMPONENT-LEVEL RULES
    # --------------------------------------------------
    for comp in design.get("components", []):
        val = comp.get("value", "").lower()

        comp_rules = get_component_rules(val)

        if comp_rules:
            comp["rules"] = comp_rules

    # --------------------------------------------------
    # APPLY ROUTE RULES
    # --------------------------------------------------
    for route in design.get("routes", []):
        width = route.get("width", 0)

        min_width = default_rules.get("min_trace_width", 0.2)

        if width < min_width:
            route["width"] = min_width

    logger.info("Rules applied successfully")

    return design


# --------------------------------------------------
# VALIDATE RULE COMPLIANCE
# --------------------------------------------------
def validate_rules(design: Dict[str, Any]) -> List[Dict]:
    """
    Check if design violates constraints
    """

    violations = []

    rules = design.get("constraints", {})

    min_width = rules.get("min_trace_width", 0.2)
    min_clearance = rules.get("min_clearance", 0.2)

    # Check trace widths
    for route in design.get("routes", []):
        if route.get("width", 0) < min_width:
            violations.append({
                "type": "trace_width",
                "message": f"Trace width too small for {route.get('net')}"
            })

    # Check simple overlap (layout)
    positions = {}
    for ref, pos in design.get("layout", {}).items():
        key = (pos.get("x"), pos.get("y"))

        if key in positions:
            violations.append({
                "type": "overlap",
                "message": f"Overlap detected: {ref} and {positions[key]}"
            })

        positions[key] = ref

    return violations


# --------------------------------------------------
# RULE ENGINE CLASS (ADVANCED)
# --------------------------------------------------
class RuleEngine:

    def __init__(self, custom_rules: Dict[str, Any] = None):
        self.rules = RULE_DB.copy()

        if custom_rules:
            self.rules.update(custom_rules)

    def apply(self, design: Dict[str, Any]) -> Dict[str, Any]:
        return apply_rules(design)

    def validate(self, design: Dict[str, Any]) -> Dict[str, Any]:
        violations = validate_rules(design)

        return {
            "status": "PASS" if not violations else "FAIL",
            "violations": violations
        }


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample = {
        "components": [{"ref": "R1", "value": "10k"}],
        "nets": [{"name": "SIG", "connections": ["R1:1"]}],
        "routes": [{"net": "SIG", "path": [(0, 0), (10, 10)], "width": 0.1}],
        "layout": {
            "R1": {"x": 0, "y": 0},
            "R2": {"x": 0, "y": 0}
        }
    }

    design = apply_rules(sample)
    result = validate_rules(design)

    from pprint import pprint
    pprint(result)
  
