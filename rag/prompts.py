# rag/prompts.py

from typing import List, Dict, Any


# --------------------------------------------------
# BASE SYSTEM PROMPT
# --------------------------------------------------
SYSTEM_PROMPT = """
You are an expert PCB design engineer.

You understand:
- Electronics (analog + digital)
- PCB layout and routing
- Signal integrity
- Power systems
- DRC and manufacturing constraints

Always:
- Be precise
- Use engineering reasoning
- Avoid vague answers
"""


# --------------------------------------------------
# DESIGN SUMMARY BUILDER
# --------------------------------------------------
def build_design_summary(design: Dict[str, Any]) -> str:
    return f"""
Components: {len(design.get("components", []))}
Nets: {len(design.get("nets", []))}
Routes: {len(design.get("routes", []))}
Placed: {len(design.get("layout", {}))}
"""


# --------------------------------------------------
# CONTEXT BUILDER
# --------------------------------------------------
def build_context(docs: List[Dict[str, Any]]) -> str:
    return "\n".join([d["text"] for d in docs])


# --------------------------------------------------
# MAIN QA PROMPT
# --------------------------------------------------
def build_qa_prompt(
    query: str,
    design: Dict[str, Any],
    docs: List[Dict[str, Any]]
) -> str:
    return f"""
{SYSTEM_PROMPT}

Design Summary:
{build_design_summary(design)}

Context:
{build_context(docs)}

User Question:
{query}

Provide a clear, technical answer.
"""


# --------------------------------------------------
# CHAT PROMPT WITH MEMORY
# --------------------------------------------------
def build_chat_prompt(
    query: str,
    design: Dict[str, Any],
    docs: List[Dict[str, Any]],
    history: List[Dict[str, str]]
) -> str:
    history_text = "\n".join([
        f"{m['role']}: {m['content']}" for m in history[-5:]
    ])

    return f"""
{SYSTEM_PROMPT}

Conversation History:
{history_text}

Design Summary:
{build_design_summary(design)}

Context:
{build_context(docs)}

User:
{query}

Assistant:
"""


# --------------------------------------------------
# DEBUGGING PROMPT
# --------------------------------------------------
def build_debug_prompt(
    design: Dict[str, Any],
    drc_errors: List[Dict]
) -> str:
    return f"""
{SYSTEM_PROMPT}

The PCB design has the following issues:

{drc_errors}

Design Summary:
{build_design_summary(design)}

Explain:
- What is wrong
- Why it is wrong
- How to fix it
"""


# --------------------------------------------------
# LAYOUT OPTIMIZATION PROMPT
# --------------------------------------------------
def build_layout_prompt(design: Dict[str, Any]) -> str:
    return f"""
{SYSTEM_PROMPT}

Given this PCB design:

{build_design_summary(design)}

Suggest:
- Better component placement
- Power distribution improvements
- Thermal considerations
"""


# --------------------------------------------------
# ROUTING OPTIMIZATION PROMPT
# --------------------------------------------------
def build_routing_prompt(design: Dict[str, Any]) -> str:
    return f"""
{SYSTEM_PROMPT}

Analyze routing quality:

{build_design_summary(design)}

Focus on:
- Trace length
- Congestion
- Signal integrity
- Power routing

Suggest improvements.
"""


# --------------------------------------------------
# DRC FIX PROMPT
# --------------------------------------------------
def build_drc_fix_prompt(
    design: Dict[str, Any],
    drc_errors: List[Dict]
) -> str:
    return f"""
{SYSTEM_PROMPT}

Fix the following PCB design issues:

Errors:
{drc_errors}

Design:
{build_design_summary(design)}

Provide:
- Step-by-step fixes
- Updated constraints
"""


# --------------------------------------------------
# DESIGN GENERATION PROMPT
# --------------------------------------------------
def build_generation_prompt(user_input: str) -> str:
    return f"""
{SYSTEM_PROMPT}

User wants to design a PCB:

Request:
{user_input}

Generate:
- Components list
- Nets
- Basic architecture
"""


# --------------------------------------------------
# EXPLAIN DESIGN PROMPT
# --------------------------------------------------
def build_explain_prompt(design: Dict[str, Any]) -> str:
    return f"""
{SYSTEM_PROMPT}

Explain this PCB design:

{build_design_summary(design)}

Describe:
- Purpose of each component
- Signal flow
- Power flow
"""


# --------------------------------------------------
# PROMPT DEBUG VIEW
# --------------------------------------------------
def preview_prompt(prompt: str):
    """
    Utility to inspect prompt
    """
    print("\n--- PROMPT START ---\n")
    print(prompt)
    print("\n--- PROMPT END ---\n")
