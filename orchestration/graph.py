# orchestration/graph.py

from typing import Any, Dict, Callable

from orchestration.state import PCBState
from orchestration.router import route_next, run_routing_loop

# --------------------------------------------------
# AGENTS (IMPORTS)
# --------------------------------------------------
from orchestration.agents.parsing_agent import run_parsing
from orchestration.agents.normalization_agent import run_normalization
from orchestration.agents.enrichment_agent import run_enrichment
from orchestration.agents.layout_agent import run_layout
from orchestration.agents.routing_agent import run_routing
from orchestration.agents.drc_agent import run_drc
from orchestration.agents.autofix_agent import run_autofix
from orchestration.agents.rag_agent import run_rag
from orchestration.agents.render_agent import run_render


# --------------------------------------------------
# AGENT REGISTRY
# --------------------------------------------------
def get_agent_map() -> Dict[str, Callable]:
    """
    Map route keys → agent functions
    """
    return {
        "parsing": run_parsing,
        "normalization": run_normalization,
        "enrichment": run_enrichment,
        "layout": run_layout,
        "routing": run_routing,
        "drc": run_drc,
        "autofix": run_autofix,
        # Optional / terminal steps
        "rag": run_rag,
        "render": run_render,
    }


# --------------------------------------------------
# HOOKS (EXTENSIBILITY)
# --------------------------------------------------
def _pre_step(state: PCBState, step: str):
    state.set_stage(step)
    state.log(f"→ Executing: {step}")


def _post_step(state: PCBState, step: str):
    state.log(f"✓ Completed: {step}")
    # Snapshot after each step for debugging/rollback
    state.snapshot(label=step)


def _on_error(state: PCBState, step: str, err: Exception):
    state.add_error(f"{step}: {str(err)}")
    state.log(f"✗ Error in {step}: {err}", level="ERROR")


# --------------------------------------------------
# CORE EXECUTOR (DYNAMIC)
# --------------------------------------------------
def run_graph(input_data: Any, max_steps: int = 50) -> PCBState:
    """
    Dynamic multi-agent execution loop (LangGraph-style)
    """

    state = PCBState(initial_input=input_data)
    agent_map = get_agent_map()

    step_count = 0
    state.set_status("RUNNING")

    while True:
        # Safety guard
        if step_count >= max_steps:
            state.add_error("Max steps exceeded")
            break

        # Decide next step
        step = route_next(state)

        if step == "end":
            break

        if step not in agent_map:
            state.add_error(f"Unknown step: {step}")
            break

        # Execute step
        try:
            _pre_step(state, step)

            agent_fn = agent_map[step]
            agent_fn(state)

            _post_step(state, step)

        except Exception as e:
            _on_error(state, step, e)

        step_count += 1

    # Optional finalization
    try:
        if "design" in state and state.get("design"):
            # Load RAG context
            run_rag(state)

            # Render output (non-blocking)
            try:
                run_render(state)
            except Exception:
                pass
    except Exception:
        pass

    # Final status
    if state.has_errors():
        state.set_status("COMPLETED_WITH_ERRORS")
    else:
        state.set_status("DONE")

    state.log("Pipeline finished")

    return state


# --------------------------------------------------
# ONE-SHOT (CONVENIENCE)
# --------------------------------------------------
def run_once(input_data: Any) -> Dict[str, Any]:
    """
    Run graph and return only design
    """
    state = run_graph(input_data)
    return state.get_design()


# --------------------------------------------------
# DEBUG RUN
# --------------------------------------------------
if __name__ == "__main__":
    sample = {
        "components": [{"ref": "R1", "value": "10k"}],
        "nets": [{"name": "SIG", "connections": ["R1:1"]}]
    }

    state = run_graph(sample)

    print("\n=== FINAL STATE ===")
    state.debug_print()
    print("Summary:", state.summary())
  
