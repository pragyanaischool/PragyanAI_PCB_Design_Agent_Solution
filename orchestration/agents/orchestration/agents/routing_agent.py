# orchestration/agents/routing_agent.py

from typing import Dict, Any, List

from generation.routing.autorouter import autoroute
from generation.routing.manhattan import manhattan_route


# ==================================================
# VALIDATION
# ==================================================
def _validate_routes(design: Dict[str, Any]) -> List[str]:
    errors = []

    routes = design.get("routes", [])
    nets = design.get("nets", [])

    if not routes:
        errors.append("No routes generated")

    for net in nets:
        name = net.get("name")

        # Check if net has at least one route
        if not any(r.get("net") == name for r in routes):
            errors.append(f"Net {name} not routed")

    return errors


# ==================================================
# POWER ROUTING PRIORITY
# ==================================================
def _prioritize_power_nets(design: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mark power nets for special routing
    """

    for net in design.get("nets", []):
        name = net.get("name", "").lower()

        if name in ["vcc", "gnd", "power"]:
            net["priority"] = "high"
        else:
            net["priority"] = "normal"

    return design


# ==================================================
# SAFE AUTOROUTER
# ==================================================
def _safe_autoroute(design: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return autoroute(design)
    except Exception:
        # Fallback to Manhattan routing
        return manhattan_route(design)


# ==================================================
# MAIN AGENT
# ==================================================
def run_routing(state):
    """
    Routing Agent:
    - Routes nets between components
    - Applies power-aware routing
    - Validates routing
    """

    try:
        state.set_stage("routing")
        state.log("Routing started")

        design = state.get_design()

        if not design:
            raise ValueError("No design available for routing")

        # --------------------------------------------------
        # PRIORITIZE POWER NETS
        # --------------------------------------------------
        design = _prioritize_power_nets(design)

        # --------------------------------------------------
        # ROUTE
        # --------------------------------------------------
        design = _safe_autoroute(design)

        # --------------------------------------------------
        # VALIDATION
        # --------------------------------------------------
        errors = _validate_routes(design)

        if errors:
            state.log(f"Routing warnings: {errors}", level="WARNING")

        # --------------------------------------------------
        # UPDATE STATE
        # --------------------------------------------------
        state.update_design(design)
        state["routing_done"] = True

        # Snapshot
        state.snapshot("routing")

        # Logging
        routes = len(design.get("routes", []))
        state.log(f"Routing complete: {routes} routes generated")

    except Exception as e:
        state.add_error(f"Routing failed: {str(e)}")
        state.log("Routing error occurred", level="ERROR")
      
