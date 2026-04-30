# orchestration/agents/drc_agent.py

from typing import Dict, Any, List
from generation.drc.checks import run_drc


# ==================================================
# DRC SUMMARY
# ==================================================
def _summarize_drc(drc_results: List[Dict[str, Any]]) -> Dict[str, int]:
    summary = {
        "total": len(drc_results),
        "errors": 0,
        "warnings": 0
    }

    for r in drc_results:
        level = r.get("level", "error").lower()

        if level == "warning":
            summary["warnings"] += 1
        else:
            summary["errors"] += 1

    return summary


# ==================================================
# MAIN AGENT
# ==================================================
def run_drc(state):
    """
    DRC Agent:
    - Runs design rule checks
    - Detects violations
    - Summarizes issues
    """

    try:
        state.set_stage("drc")
        state.log("DRC check started")

        design = state.get_design()

        if not design:
            raise ValueError("No design available for DRC")

        # --------------------------------------------------
        # RUN DRC
        # --------------------------------------------------
        drc_results = run_drc(design)

        design["drc"] = drc_results

        # --------------------------------------------------
        # SUMMARY
        # --------------------------------------------------
        summary = _summarize_drc(drc_results)
        design["drc_summary"] = summary

        # --------------------------------------------------
        # UPDATE STATE
        # --------------------------------------------------
        state.update_design(design)
        state["drc_done"] = True

        # Snapshot
        state.snapshot("drc")

        state.log(f"DRC complete: {summary}")

    except Exception as e:
        state.add_error(f"DRC failed: {str(e)}")
        state.log("DRC error occurred", level="ERROR")
      
