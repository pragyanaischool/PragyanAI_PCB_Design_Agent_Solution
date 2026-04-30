# orchestration/agents/autofix_agent.py

from typing import Dict, Any
from generation.autofix.fixer import auto_fix


# ==================================================
# SHOULD FIX?
# ==================================================
def _needs_fix(design: Dict[str, Any]) -> bool:
    drc = design.get("drc", [])
    return len(drc) > 0


# ==================================================
# MAIN AGENT
# ==================================================
def run_autofix(state):
    """
    AutoFix Agent:
    - Fixes DRC violations
    - Iteratively improves design
    """

    try:
        state.set_stage("autofix")
        state.log("Auto-fix started")

        design = state.get_design()

        if not design:
            raise ValueError("No design available for autofix")

        if not _needs_fix(design):
            state.log("No fixes required")
            return

        # --------------------------------------------------
        # APPLY FIX
        # --------------------------------------------------
        fixed_design = auto_fix(design)

        # --------------------------------------------------
        # UPDATE STATE
        # --------------------------------------------------
        state.update_design(fixed_design)
        state["autofix_done"] = True

        # Snapshot
        state.snapshot("autofix")

        state.log("Auto-fix applied successfully")

    except Exception as e:
        state.add_error(f"AutoFix failed: {str(e)}")
        state.log("AutoFix error occurred", level="ERROR")
      
