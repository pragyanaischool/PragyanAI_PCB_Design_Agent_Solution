# orchestration/agents/normalization_agent.py

from typing import Dict, Any, List

from normalization.normalize import normalize_design
from normalization.validator import validate_design


# ==================================================
# POST-NORMALIZATION CLEANUP
# ==================================================
def _clean_components(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize component fields
    """
    cleaned = []

    for c in components:
        comp = {
            "ref": str(c.get("ref", "")).upper(),
            "value": str(c.get("value", "")).upper(),
            "footprint": c.get("footprint", ""),
            "pins": c.get("pins", [])
        }

        cleaned.append(comp)

    return cleaned


def _clean_nets(nets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize net structure
    """
    cleaned = []

    for n in nets:
        net = {
            "name": str(n.get("name", "")).upper(),
            "connections": list(set(n.get("connections", [])))
        }

        cleaned.append(net)

    return cleaned


# ==================================================
# MAIN AGENT
# ==================================================
def run_normalization(state):
    """
    Normalization Agent:
    - Standardizes design schema
    - Cleans data
    - Validates structure
    """

    try:
        state.set_stage("normalization")
        state.log("Normalization started")

        design = state.get_design()

        if not design:
            raise ValueError("No design available for normalization")

        # --------------------------------------------------
        # CORE NORMALIZATION
        # --------------------------------------------------
        design = normalize_design(design)

        # --------------------------------------------------
        # CLEAN COMPONENTS & NETS
        # --------------------------------------------------
        design["components"] = _clean_components(
            design.get("components", [])
        )

        design["nets"] = _clean_nets(
            design.get("nets", [])
        )

        # --------------------------------------------------
        # VALIDATION
        # --------------------------------------------------
        valid, errors = validate_design(design)

        if not valid:
            state.log(f"Validation warnings: {errors}", level="WARNING")

        # --------------------------------------------------
        # UPDATE STATE
        # --------------------------------------------------
        state.update_design(design)
        state["normalized"] = True

        # Snapshot
        state.snapshot("normalized")

        # Logging
        comps = len(design.get("components", []))
        nets = len(design.get("nets", []))

        state.log(f"Normalization complete: {comps} components, {nets} nets")

    except Exception as e:
        state.add_error(f"Normalization failed: {str(e)}")
        state.log("Normalization error occurred", level="ERROR")
      
