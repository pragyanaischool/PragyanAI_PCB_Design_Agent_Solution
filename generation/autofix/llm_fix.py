# generation/autofix/llm_fix.py

from typing import Dict, Any, List
import json

from utils.logger import get_module_logger
from config.settings import settings

logger = get_module_logger(__name__)


# --------------------------------------------------
# SAFE IMPORT GROQ CLIENT
# --------------------------------------------------
def get_llm_client():
    try:
        from orchestration.llm.groq_client import get_groq_client
        return get_groq_client()
    except Exception as e:
        logger.warning(f"Groq client not available: {e}")
        return None


# --------------------------------------------------
# PROMPT TEMPLATE
# --------------------------------------------------
def build_prompt(design: Dict[str, Any], errors: List[Dict[str, Any]]) -> str:
    return f"""
You are an expert PCB design engineer.

Given the following PCB design and DRC errors, suggest fixes.

Return ONLY valid JSON in this format:
{{
  "actions": [
    {{
      "type": "move_component",
      "ref": "R1",
      "dx": 10,
      "dy": 5
    }},
    {{
      "type": "increase_trace_width",
      "net": "VCC",
      "width": 0.3
    }}
  ]
}}

Design:
{json.dumps(design, indent=2)}

Errors:
{json.dumps(errors, indent=2)}
"""


# --------------------------------------------------
# SAFE JSON PARSER
# --------------------------------------------------
def safe_parse_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        try:
            # Attempt to extract JSON substring
            start = text.find("{")
            end = text.rfind("}") + 1
            return json.loads(text[start:end])
        except Exception as e:
            logger.error(f"Failed to parse LLM JSON: {e}")
            return {"actions": []}


# --------------------------------------------------
# APPLY LLM ACTIONS
# --------------------------------------------------
def apply_actions(design: Dict[str, Any], actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    layout = design.get("layout", {})
    routes = design.get("routes", [])

    for action in actions:
        atype = action.get("type")

        # Move component
        if atype == "move_component":
            ref = action.get("ref")
            dx = action.get("dx", 0)
            dy = action.get("dy", 0)

            if ref in layout:
                layout[ref]["x"] += dx
                layout[ref]["y"] += dy

        # Increase trace width
        elif atype == "increase_trace_width":
            net = action.get("net")
            width = action.get("width", settings.MIN_TRACE_WIDTH)

            for route in routes:
                if route.get("net") == net:
                    route["width"] = max(route.get("width", 0), width)

        # Re-route net
        elif atype == "reroute_net":
            from generation.routing.autorouter import autoroute
            design = autoroute(design)

        # Global shift (spread components)
        elif atype == "spread_layout":
            for ref in layout:
                layout[ref]["x"] += 5
                layout[ref]["y"] += 5

    return design


# --------------------------------------------------
# MAIN LLM FIX FUNCTION
# --------------------------------------------------
def llm_fix(design: Dict[str, Any], errors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Use Groq LLM to suggest fixes and apply them
    """

    client = get_llm_client()

    if not client:
        logger.info("Skipping LLM fix (client unavailable)")
        return design

    try:
        prompt = build_prompt(design, errors)

        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=settings.LLM_TEMPERATURE,
        )

        content = response.choices[0].message.content

        parsed = safe_parse_json(content)
        actions = parsed.get("actions", [])

        logger.info(f"LLM suggested {len(actions)} actions")

        design = apply_actions(design, actions)

        return design

    except Exception as e:
        logger.error(f"LLM fix failed: {e}")
        return design


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample_design = {
        "components": [
            {"ref": "R1", "value": "10k"},
            {"ref": "C1", "value": "100nF"},
        ],
        "layout": {
            "R1": {"x": 10, "y": 10},
            "C1": {"x": 10, "y": 10},
        },
        "routes": [
            {"net": "VCC", "width": 0.1}
        ],
        "nets": []
    }

    sample_errors = [
        {"type": "OVERLAP", "refs": ["R1", "C1"]},
        {"type": "TRACE_WIDTH", "net": "VCC"}
    ]

    updated = llm_fix(sample_design, sample_errors)

    print(updated)
  
