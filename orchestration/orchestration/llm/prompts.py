# orchestration/llm/prompts.py

from typing import Dict, Any, List


# ==================================================
# SYSTEM PROMPT (GLOBAL IDENTITY)
# ==================================================
SYSTEM_PROMPT = """
You are an expert PCB design AI system.

You specialize in:
- Circuit design (analog + digital)
- PCB layout and routing
- Signal integrity & power distribution
- EMI/EMC and thermal design
- Design rule checking (DRC)

Guidelines:
- Be precise and technical
- Provide actionable steps
- Avoid vague responses
- Think like a hardware engineer
"""


# ==================================================
# DESIGN SUMMARY
# ==================================================
def build_design_summary(design: Dict[str, Any]) -> str:
    return f"""
Components: {len(design.get("components", []))}
Nets: {len(design.get("nets", []))}
Routes: {len(design.get("routes", []))}
Placed: {len(design.get("layout", {}))}
"""


# ==================================================
# GENERIC AGENT PROMPT
# ==================================================
def build_agent_prompt(task: str, design: Dict[str, Any]) -> str:
    return f"""
{SYSTEM_PROMPT}

Task:
{task}

Design Summary:
{build_design_summary(design)}

Provide a clear and technical response.
"""


# ==================================================
# LAYOUT PROMPT
# ==================================================
def build_layout_prompt(design: Dict[str, Any]) -> str:
    return f"""
{SYSTEM_PROMPT}

Optimize PCB component placement.

Design:
{build_design_summary(design)}

Focus on:
- Power distribution
- Thermal separation
- Signal clustering

Provide placement strategy.
"""


# ==================================================
# ROUTING PROMPT
# ==================================================
def build_routing_prompt(design: Dict[str, Any]) -> str:
    return f"""
{SYSTEM_PROMPT}

Analyze routing quality.

Design:
{build_design_summary(design)}

Focus on:
- Trace length
- Crosstalk
- Power routing
- Congestion

Suggest improvements.
"""


# ==================================================
# DRC DEBUG PROMPT
# ==================================================
def build_drc_prompt(
    design: Dict[str, Any],
    drc_errors: List[Dict[str, Any]]
) -> str:
    return f"""
{SYSTEM_PROMPT}

The PCB has the following DRC issues:
{drc_errors}

Design:
{build_design_summary(design)}

Explain:
1. Root cause
2. Impact
3. Fix strategy
"""


# ==================================================
# AUTOFIX PROMPT
# ==================================================
def build_autofix_prompt(
    design: Dict[str, Any],
    drc_errors: List[Dict[str, Any]]
) -> str:
    return f"""
{SYSTEM_PROMPT}

Fix the PCB design issues:

Errors:
{drc_errors}

Design:
{build_design_summary(design)}

Provide:
- Exact fixes
- Updated layout/routing suggestions
"""


# ==================================================
# RAG QA PROMPT
# ==================================================
def build_rag_prompt(
    query: str,
    context: str,
    design: Dict[str, Any]
) -> str:
    return f"""
{SYSTEM_PROMPT}

Context:
{context}

Design:
{build_design_summary(design)}

User Question:
{query}

Answer with technical reasoning.
"""


# ==================================================
# DESIGN GENERATION PROMPT
# ==================================================
def build_generation_prompt(user_input: str) -> str:
    return f"""
{SYSTEM_PROMPT}

User wants to design a PCB:

Request:
{user_input}

Generate:
- Components list
- Net connections
- Architecture
- Power design considerations
"""


# ==================================================
# EXPLAIN DESIGN PROMPT
# ==================================================
def build_explain_prompt(design: Dict[str, Any]) -> str:
    return f"""
{SYSTEM_PROMPT}

Explain this PCB design:

{build_design_summary(design)}

Explain:
- Purpose of each component
- Signal flow
- Power flow
"""


# ==================================================
# STRUCTURED OUTPUT PROMPT (FOR AGENTS)
# ==================================================
def build_structured_prompt(
    task: str,
    context: str
) -> str:
    return f"""
{SYSTEM_PROMPT}

Task:
{task}

Context:
{context}

Return JSON:
{{
  "analysis": "...",
  "recommendations": ["..."],
  "actions": ["..."]
}}
"""


# ==================================================
# TOOL CALL PROMPT
# ==================================================
def build_tool_prompt(
    tool_name: str,
    tool_input: Dict[str, Any]
) -> str:
    return f"""
{SYSTEM_PROMPT}

Use tool:
{tool_name}

Input:
{tool_input}

Explain what the tool should do and expected output.
"""


# ==================================================
# CHAT PROMPT (WITH MEMORY)
# ==================================================
def build_chat_prompt(
    query: str,
    history: List[Dict[str, str]],
    design: Dict[str, Any]
) -> str:
    history_text = "\n".join(
        [f"{m['role']}: {m['content']}" for m in history[-5:]]
    )

    return f"""
{SYSTEM_PROMPT}

Conversation History:
{history_text}

Design:
{build_design_summary(design)}

User:
{query}

Assistant:
"""


# ==================================================
# PROMPT DEBUG TOOL
# ==================================================
def preview_prompt(prompt: str):
    print("\n===== PROMPT START =====\n")
    print(prompt)
    print("\n===== PROMPT END =====\n")
  
