# orchestration/router.py

from typing import Dict, Any


# ==================================================
# CORE ROUTER
# ==================================================
def route_next(state: Dict[str, Any]) -> str:
    """
    Decide next agent based on current state
    """

    design = state.get("design", {})
    errors = state.get("errors", [])
    stage = state.get("stage", "")

    # --------------------------------------------------
    # ERROR HANDLING
    # --------------------------------------------------
    if errors:
        return "autofix"

    # --------------------------------------------------
    # INITIAL FLOW
    # --------------------------------------------------
    if not design:
        return "parsing"

    if "normalized" not in state:
        return "normalization"

    if not _is_enriched(design):
        return "enrichment"

    if "layout" not in design:
        return "layout"

    if "routes" not in design:
        return "routing"

    if "drc" not in design:
        return "drc"

    # --------------------------------------------------
    # DRC CHECK
    # --------------------------------------------------
    if design.get("drc"):
        # If DRC errors exist → fix
        if len(design["drc"]) > 0:
            return "autofix"

    # --------------------------------------------------
    # FINAL
    # --------------------------------------------------
    return "end"


# ==================================================
# ENRICHMENT CHECK
# ==================================================
def _is_enriched(design: Dict[str, Any]) -> bool:
    """
    Check if components have pins + footprints
    """
    comps = design.get("components", [])

    for c in comps:
        if "pins" not in c:
            return False
        if "footprint" not in c:
            return False

    return True


# ==================================================
# LOOP CONTROL (DRC → FIX → RECHECK)
# ==================================================
def should_continue(state: Dict[str, Any], max_loops: int = 3) -> bool:
    """
    Prevent infinite loops
    """

    loops = state.get("loop_count", 0)

    if loops >= max_loops:
        return False

    design = state.get("design", {})

    if design.get("drc") and len(design["drc"]) > 0:
        return True

    return False


def increment_loop(state: Dict[str, Any]):
    state["loop_count"] = state.get("loop_count", 0) + 1


# ==================================================
# ROUTE EXECUTION MAP
# ==================================================
ROUTE_MAP = {
    "parsing": "run_parsing",
    "normalization": "run_normalization",
    "enrichment": "run_enrichment",
    "layout": "run_layout",
    "routing": "run_routing",
    "drc": "run_drc",
    "autofix": "run_autofix",
    "rag": "run_rag",
    "render": "run_render",
    "end": None
}


# ==================================================
# DEBUG ROUTER
# ==================================================
def debug_route(state: Dict[str, Any]):
    next_step = route_next(state)

    print("\n===== ROUTER =====")
    print("Current Stage:", state.get("stage"))
    print("Next Step:", next_step)
    print("Errors:", len(state.get("errors", [])))
    print("==================\n")

    return next_step


# ==================================================
# FULL ROUTING LOOP (OPTIONAL EXECUTOR)
# ==================================================
def run_routing_loop(state, agent_map: Dict[str, Any]):
    """
    Dynamic execution loop (LangGraph-like)
    """

    state["loop_count"] = 0

    while True:
        step = route_next(state)

        if step == "end":
            break

        if step not in agent_map:
            state["errors"].append(f"Unknown step: {step}")
            break

        # Execute agent
        agent_fn = agent_map[step]
        agent_fn(state)

        # Loop control for DRC fixes
        if step == "autofix":
            increment_loop(state)

            if not should_continue(state):
                break

    return state
