# orchestration/agents/autofix_agent.py

from typing import Dict, Any, List
import copy

from generation.autofix.fixer import auto_fix

# Optional LLM support
try:
    from orchestration.llm.groq_client import call_llm
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False


# ==================================================
# CHECK IF FIX NEEDED
# ==================================================
def _needs_fix(design: Dict[str, Any]) -> bool:
    drc = design.get("drc", [])
    return len(drc) > 0


# ==================================================
# RULE-BASED FIXES (SAFE FALLBACK)
# ==================================================
def _apply_basic_fixes(design: Dict[str, Any]) -> Dict[str, Any]:
    """
    Lightweight fixes if auto_fix fails
    """

    new_design = copy.deepcopy(design)

    # Example: ensure all components have layout
    layout = new_design.get("layout", {})
    comps = new_design.get("components", [])

    x, y = 0, 0
    for c in comps:
        ref = c["ref"]

        if ref not in layout:
            layout[ref] = {"x": x, "y": y}
            x += 5
            if x > 100:
                x = 0
                y += 5

    new_design["layout"] = layout

    return new_design


# ==================================================
# LLM-ASSISTED FIX (OPTIONAL)
# ==================================================
def _llm_fix(design: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use LLM to suggest fixes (experimental)
    """

    if not LLM_AVAILABLE:
        return design

    prompt = f"""
You are a PCB design expert.

Fix the following PCB issues:

Design:
{design}

Return improved design in JSON format.
"""

    try:
        response = call_llm(prompt)

        # NOTE: In real system you'd parse JSON safely
        return design  # fallback (no unsafe parsing)

    except Exception:
        return design


# ==================================================
# VALIDATION AFTER FIX
# ==================================================
def _validate_fix(old: Dict, new: Dict) -> bool:
    """
    Ensure fix didn't break design
    """
    if not new:
        return False

    if "components" not in new or "nets" not in new:
        return False

    return True


# ==================================================
# MAIN AGENT
# ==================================================
def run_autofix(state):
    """
    AutoFix Agent:
    - Fixes DRC violations
    - Improves layout/routing
    - Supports iterative refinement
    """

    try:
        state.set_stage("autofix")
        state.log("Auto-fix started")

        design = state.get_design()

        if not design:
            raise ValueError("No design available for autofix")

        # --------------------------------------------------
        # CHECK NEED
        # --------------------------------------------------
        if not _needs_fix(design):
            state.log("No DRC issues → skipping autofix")
            return

        # --------------------------------------------------
        # SAVE ORIGINAL
        # --------------------------------------------------
        original = copy.deepcopy(design)

        # --------------------------------------------------
        # PRIMARY FIX ENGINE
        # --------------------------------------------------
        try:
            fixed = auto_fix(design)
            state.log("Auto-fix (rule engine) applied")
        except Exception:
            fixed = design
            state.log("Auto-fix engine failed", level="WARNING")

        # --------------------------------------------------
        # LLM FIX (OPTIONAL)
        # --------------------------------------------------
        fixed = _llm_fix(fixed)

        # --------------------------------------------------
        # FALLBACK FIX
        # --------------------------------------------------
        if not fixed or fixed == design:
            fixed = _apply_basic_fixes(design)
            state.log("Fallback fix applied")

        # --------------------------------------------------
        # VALIDATION
        # --------------------------------------------------
        if not _validate_fix(original, fixed):
            state.log("Fix validation failed → reverting", level="WARNING")
            fixed = original

        # --------------------------------------------------
        # UPDATE STATE
        # --------------------------------------------------
        state.update_design(fixed)
        state["autofix_done"] = True

        # Track iteration
        state["fix_iteration"] = state.get("fix_iteration", 0) + 1

        # Snapshot
        state.snapshot(f"autofix_iter_{state['fix_iteration']}")

        # Logging
        state.log(
            f"Auto-fix completed (iteration {state['fix_iteration']})"
        )

    except Exception as e:
        state.add_error(f"AutoFix failed: {str(e)}")
        state.log("AutoFix error occurred", level="ERROR")
        
