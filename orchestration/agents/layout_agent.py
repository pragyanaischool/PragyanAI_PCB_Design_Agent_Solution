# orchestration/agents/layout_agent.py

from typing import Dict, Any, List

from generation.layout.auto_place import auto_place


# ==================================================
# VALIDATION
# ==================================================
def _validate_layout(design: Dict[str, Any]) -> List[str]:
    errors = []

    layout = design.get("layout", {})
    components = design.get("components", [])

    for c in components:
        ref = c.get("ref")

        if ref not in layout:
            errors.append(f"{ref}: not placed")

        else:
            pos = layout[ref]
            if "x" not in pos or "y" not in pos:
                errors.append(f"{ref}: invalid position")

    return errors


# ==================================================
# POWER / THERMAL HEURISTICS (LIGHTWEIGHT)
# ==================================================
def _tag_special_components(components: List[Dict[str, Any]]):
    """
    Identify power / thermal components for better placement
    """

    for c in components:
        val = str(c.get("value", "")).lower()

        # Power regulators / VCC drivers
        if any(k in val for k in ["reg", "7805", "vcc", "power"]):
            c["placement_hint"] = "power_zone"

        # Heat-generating components
        elif any(k in val for k in ["mosfet", "driver", "amp"]):
            c["placement_hint"] = "thermal_zone"

        else:
            c["placement_hint"] = "signal_zone"

    return components


# ==================================================
# SAFE AUTO PLACE
# ==================================================
def _safe_auto_place(design: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return auto_place(design)
    except Exception:
        # Fallback: naive grid placement
        layout = {}
        x, y = 0, 0

        for c in design.get("components", []):
            layout[c["ref"]] = {"x": x, "y": y}
            x += 10
            if x > 100:
                x = 0
                y += 10

        design["layout"] = layout
        return design


# ==================================================
# MAIN AGENT
# ==================================================
def run_layout(state):
    """
    Layout Agent:
    - Places components
    - Applies heuristics
    - Ensures layout completeness
    """

    try:
        state.set_stage("layout")
        state.log("Layout started")

        design = state.get_design()

        if not design:
            raise ValueError("No design available for layout")

        # --------------------------------------------------
        # TAG COMPONENTS (power / thermal / signal)
        # --------------------------------------------------
        components = design.get("components", [])
        components = _tag_special_components(components)
        design["components"] = components

        # --------------------------------------------------
        # AUTO PLACE
        # --------------------------------------------------
        design = _safe_auto_place(design)

        # --------------------------------------------------
        # VALIDATION
        # --------------------------------------------------
        errors = _validate_layout(design)

        if errors:
            state.log(f"Layout warnings: {errors}", level="WARNING")

        # --------------------------------------------------
        # UPDATE STATE
        # --------------------------------------------------
        state.update_design(design)
        state["layout_done"] = True

        # Snapshot
        state.snapshot("layout")

        # Logging
        placed = len(design.get("layout", {}))
        state.log(f"Layout complete: {placed} components placed")

    except Exception as e:
        state.add_error(f"Layout failed: {str(e)}")
        state.log("Layout error occurred", level="ERROR")
      
