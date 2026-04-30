# orchestration/agents/parsing_agent.py

from typing import Any, Dict
from parsing.router import parse_input


# ==================================================
# VALIDATION
# ==================================================
def _validate_design(design: Dict[str, Any]) -> bool:
    """
    Basic sanity check after parsing
    """
    if not isinstance(design, dict):
        return False

    if "components" not in design or "nets" not in design:
        return False

    return True


# ==================================================
# INPUT NORMALIZATION
# ==================================================
def _prepare_input(input_data: Any) -> Any:
    """
    Normalize input for parser
    """

    # Case 1: already dict
    if isinstance(input_data, dict):
        return input_data

    # Case 2: file path (str)
    if isinstance(input_data, str):
        return input_data

    raise ValueError("Unsupported input type for parsing")


# ==================================================
# MAIN AGENT
# ==================================================
def run_parsing(state):
    """
    Parsing Agent:
    - Reads input
    - Converts to raw design format
    """

    try:
        state.set_stage("parsing")
        state.log("Parsing started")

        # --------------------------------------------------
        # PREPARE INPUT
        # --------------------------------------------------
        input_data = _prepare_input(state.get("input"))

        # --------------------------------------------------
        # PARSE
        # --------------------------------------------------
        design = parse_input(input_data)

        # --------------------------------------------------
        # VALIDATE
        # --------------------------------------------------
        if not _validate_design(design):
            raise ValueError("Parsed design is invalid")

        # --------------------------------------------------
        # UPDATE STATE
        # --------------------------------------------------
        state.update_design(design)
        state["parsed"] = True

        # Snapshot
        state.snapshot("parsed")

        # Logging
        comps = len(design.get("components", []))
        nets = len(design.get("nets", []))

        state.log(f"Parsing completed: {comps} components, {nets} nets")

    except Exception as e:
        state.add_error(f"Parsing failed: {str(e)}")
        state.log("Parsing error occurred", level="ERROR")
      
