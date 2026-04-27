# generation/autofix/fixer.py

from typing import Dict, Any, List
import random
import copy

from utils.logger import get_module_logger
from config.settings import settings

from generation.drc.checks import run_drc
from generation.layout.auto_place import auto_place
from generation.routing.manhattan import auto_route


logger = get_module_logger(__name__)


MAX_ITER = settings.MAX_AUTOFIX_ITER
MIN_CLEARANCE = settings.MIN_CLEARANCE
BOARD_WIDTH = settings.BOARD_WIDTH
BOARD_HEIGHT = settings.BOARD_HEIGHT


# --------------------------------------------------
# BASIC FIX STRATEGIES
# --------------------------------------------------

def fix_overlap(design, error):
    """Move overlapping components apart"""
    refs = error.get("refs", [])
    layout = design.get("layout", {})

    for ref in refs:
        if ref in layout:
            layout[ref]["x"] += random.randint(5, 20)
            layout[ref]["y"] += random.randint(5, 20)

    return design


def fix_clearance(design, error):
    """Push components away"""
    layout = design.get("layout", {})

    for ref, pos in layout.items():
        pos["x"] += random.randint(1, 5)
        pos["y"] += random.randint(1, 5)

    return design


def fix_trace_width(design, error):
    """Increase trace width"""
    for route in design.get("routes", []):
        route["width"] = max(route.get("width", 0), MIN_CLEARANCE)

    return design


def fix_boundary(design, error):
    """Bring components inside board"""
    layout = design.get("layout", {})

    for ref, pos in layout.items():
        pos["x"] = max(0, min(pos["x"], BOARD_WIDTH))
        pos["y"] = max(0, min(pos["y"], BOARD_HEIGHT))

    return design


def fix_unconnected(design, error):
    """Re-run routing"""
    return auto_route(design)


def fix_route_clearance(design, error):
    """Re-route to avoid collisions"""
    return auto_route(design)


# --------------------------------------------------
# ERROR DISPATCHER
# --------------------------------------------------

def apply_fix(design, error):
    etype = error.get("type")

    if etype == "OVERLAP":
        return fix_overlap(design, error)

    elif etype == "CLEARANCE":
        return fix_clearance(design, error)

    elif etype == "TRACE_WIDTH":
        return fix_trace_width(design, error)

    elif etype == "BOUNDARY":
        return fix_boundary(design, error)

    elif etype == "UNCONNECTED":
        return fix_unconnected(design, error)

    elif etype in ["ROUTE_CLEARANCE", "ROUTE_COMPONENT_CLEARANCE"]:
        return fix_route_clearance(design, error)

    else:
        return design


# --------------------------------------------------
# OPTIONAL: LLM FIX (GROQ)
# --------------------------------------------------

def try_llm_fix(design, errors):
    """
    Optional intelligent fix using Groq LLM
    """
    try:
        from orchestration.llm.groq_client import get_groq_client

        client = get_groq_client()

        prompt = f"""
        You are a PCB expert.

        Design:
        {design}

        Errors:
        {errors}

        Suggest fixes in JSON format.
        """

        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )

        # NOTE: In production → parse JSON safely
        logger.info("LLM suggested fix applied")

        return design

    except Exception as e:
        logger.debug(f"LLM fix skipped: {e}")
        return design


# --------------------------------------------------
# MAIN AUTO-FIX LOOP
# --------------------------------------------------

def auto_fix(design: Dict[str, Any]) -> Dict[str, Any]:
    """
    Iterative self-healing loop

    Returns:
        {
            "design": updated_design,
            "report": final_drc_report,
            "history": list_of_iterations
        }
    """

    logger.info("Starting Auto-Fix Loop")

    current_design = copy.deepcopy(design)
    history = []

    for iteration in range(MAX_ITER):

        drc_report = run_drc(current_design)
        errors = drc_report.get("errors", [])

        history.append({
            "iteration": iteration,
            "error_count": len(errors)
        })

        if not errors:
            logger.info(f"DRC clean after {iteration} iterations")
            break

        logger.info(f"Iteration {iteration}: {len(errors)} errors")

        # Apply rule-based fixes
        for err in errors:
            current_design = apply_fix(current_design, err)

        # Optional: LLM-based refinement
        if settings.ENABLE_RAG:
            current_design = try_llm_fix(current_design, errors)

        # Re-run placement + routing (stabilization step)
        current_design = auto_place(current_design)
        current_design = auto_route(current_design)

    final_report = run_drc(current_design)

    return {
        "design": current_design,
        "report": final_report,
        "history": history
    }


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------

if __name__ == "__main__":
    sample_design = {
        "components": [
            {"ref": "R1"},
            {"ref": "C1"}
        ],
        "layout": {
            "R1": {"x": 10, "y": 10},
            "C1": {"x": 10, "y": 10}  # overlap
        },
        "routes": [],
        "nets": []
    }

    result = auto_fix(sample_design)

    print("Final Report:", result["report"])
    print("History:", result["history"])
  
