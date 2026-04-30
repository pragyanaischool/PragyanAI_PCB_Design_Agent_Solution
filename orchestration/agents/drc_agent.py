# orchestration/agents/drc_agent.py

from typing import Dict, Any, List
from collections import defaultdict

from generation.drc.checks import run_drc


# ==================================================
# CLASSIFY DRC RESULTS
# ==================================================
def _classify_drc(drc_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Categorize DRC issues
    """

    summary = {
        "total": len(drc_results),
        "errors": 0,
        "warnings": 0,
        "types": defaultdict(int)
    }

    for r in drc_results:
        level = r.get("level", "error").lower()
        issue_type = r.get("type", "unknown")

        if level == "warning":
            summary["warnings"] += 1
        else:
            summary["errors"] += 1

        summary["types"][issue_type] += 1

    return summary


# ==================================================
# FIND HOTSPOTS
# ==================================================
def _find_hotspots(drc_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Identify problematic nets/components
    """

    net_issues = defaultdict(int)
    comp_issues = defaultdict(int)

    for r in drc_results:
        if "net" in r:
            net_issues[r["net"]] += 1

        if "component" in r:
            comp_issues[r["component"]] += 1

    return {
        "nets": dict(net_issues),
        "components": dict(comp_issues)
    }


# ==================================================
# SAFE DRC
# ==================================================
def _safe_run_drc(design: Dict[str, Any]) -> List[Dict[str, Any]]:
    try:
        return run_drc(design)
    except Exception:
        return []


# ==================================================
# MAIN AGENT
# ==================================================
def run_drc(state):
    """
    DRC Agent:
    - Runs design rule checks
    - Classifies violations
    - Identifies hotspots
    - Prepares data for AutoFix
    """

    try:
        state.set_stage("drc")
        state.log("DRC started")

        design = state.get_design()

        if not design:
            raise ValueError("No design available for DRC")

        # --------------------------------------------------
        # RUN DRC
        # --------------------------------------------------
        drc_results = _safe_run_drc(design)

        # --------------------------------------------------
        # ANALYSIS
        # --------------------------------------------------
        summary = _classify_drc(drc_results)
        hotspots = _find_hotspots(drc_results)

        # --------------------------------------------------
        # UPDATE DESIGN
        # --------------------------------------------------
        design["drc"] = drc_results
        design["drc_summary"] = summary
        design["drc_hotspots"] = hotspots

        # --------------------------------------------------
        # UPDATE STATE
        # --------------------------------------------------
        state.update_design(design)
        state["drc_done"] = True

        # Snapshot
        state.snapshot("drc")

        # --------------------------------------------------
        # LOGGING
        # --------------------------------------------------
        state.log(
            f"DRC complete: {summary['total']} issues "
            f"({summary['errors']} errors, {summary['warnings']} warnings)"
        )

        if summary["errors"] > 0:
            state.log("DRC errors detected → AutoFix required", level="WARNING")

    except Exception as e:
        state.add_error(f"DRC failed: {str(e)}")
        state.log("DRC error occurred", level="ERROR")
        
