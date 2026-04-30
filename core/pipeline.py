# app/core/pipeline.py

from typing import Dict, Any, Union
import traceback

# Parsing
from parsing.router import parse_input

# Normalization
from normalization.normalize import normalize_design

# Enrichment
from enrichment.pin_mapping import map_pins
from enrichment.footprint_resolution import resolve_footprints
from enrichment.hierarchy import flatten_hierarchy
from enrichment.rules_engine import apply_rules

# Generation
from generation.layout.auto_place import auto_place
from generation.routing.autorouter import autoroute

# DRC
from generation.drc.checks import run_drc


# --------------------------------------------------
# PIPELINE CONFIG
# --------------------------------------------------
DEFAULT_CONFIG = {
    "run_drc": True,
    "debug": False
}


# --------------------------------------------------
# HELPER: DEBUG PRINT
# --------------------------------------------------
def _debug(msg: str, config: Dict):
    if config.get("debug"):
        print(f"[PIPELINE DEBUG] {msg}")


# --------------------------------------------------
# INPUT NORMALIZATION
# --------------------------------------------------
def _prepare_input(input_data: Union[str, Dict]) -> Any:
    """
    Handles multiple input formats:
    - File path (JSON, CSV, KiCad, XML)
    - Dict (CSV netlist or raw JSON)
    """

    # Case 1: direct path
    if isinstance(input_data, str):
        return input_data

    # Case 2: CSV netlist dict
    if isinstance(input_data, dict):
        if "components" in input_data and "nets" in input_data:
            return input_data

    raise ValueError("Unsupported input format for pipeline")


# --------------------------------------------------
# MAIN PIPELINE
# --------------------------------------------------
def run_pipeline(
    input_data: Union[str, Dict],
    config: Dict = None
) -> Dict[str, Any]:
    """
    End-to-end PCB design pipeline
    """

    config = config or DEFAULT_CONFIG

    try:
        _debug("Starting pipeline", config)

        # --------------------------------------------------
        # INPUT
        # --------------------------------------------------
        prepared_input = _prepare_input(input_data)
        _debug("Input prepared", config)

        # --------------------------------------------------
        # PARSING
        # --------------------------------------------------
        design = parse_input(prepared_input)
        _debug("Parsing complete", config)

        # --------------------------------------------------
        # NORMALIZATION
        # --------------------------------------------------
        design = normalize_design(design)
        _debug("Normalization complete", config)

        # --------------------------------------------------
        # HIERARCHY FLATTEN
        # --------------------------------------------------
        design = flatten_hierarchy(design)
        _debug("Hierarchy flattened", config)

        # --------------------------------------------------
        # ENRICHMENT
        # --------------------------------------------------
        design["components"] = map_pins(design.get("components", []))
        design["components"] = resolve_footprints(design.get("components", []))
        _debug("Enrichment complete", config)

        # --------------------------------------------------
        # RULES APPLICATION
        # --------------------------------------------------
        design = apply_rules(design)
        _debug("Rules applied", config)

        # --------------------------------------------------
        # LAYOUT (PLACEMENT)
        # --------------------------------------------------
        design = auto_place(design)
        _debug("Layout complete", config)

        # --------------------------------------------------
        # ROUTING
        # --------------------------------------------------
        design = autoroute(design)
        _debug("Routing complete", config)

        # --------------------------------------------------
        # DRC CHECK
        # --------------------------------------------------
        if config.get("run_drc", True):
            drc_result = run_drc(design)
            design["drc"] = drc_result
            _debug("DRC complete", config)

        _debug("Pipeline finished successfully", config)

        return design

    except Exception as e:
        traceback.print_exc()

        return {
            "error": str(e),
            "status": "FAILED"
        }


# --------------------------------------------------
# ADVANCED: PIPELINE STAGES (FOR AGENTS)
# --------------------------------------------------
def run_pipeline_stages(input_data: Union[str, Dict]) -> Dict[str, Any]:
    """
    Returns intermediate outputs for debugging or multi-agent workflows
    """

    stages = {}

    prepared_input = _prepare_input(input_data)

    stages["parsed"] = parse_input(prepared_input)
    stages["normalized"] = normalize_design(stages["parsed"])
    stages["flattened"] = flatten_hierarchy(stages["normalized"])

    comps = map_pins(stages["flattened"].get("components", []))
    comps = resolve_footprints(comps)
    stages["enriched"] = {**stages["flattened"], "components": comps}

    stages["rules"] = apply_rules(stages["enriched"])
    stages["layout"] = auto_place(stages["rules"])
    stages["routing"] = autoroute(stages["layout"])

    stages["drc"] = run_drc(stages["routing"])

    return stages


# --------------------------------------------------
# QUICK TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample = {
        "components": [{"ref": "R1", "value": "10k"}],
        "nets": [{"name": "SIG", "connections": ["R1:1"]}]
    }

    result = run_pipeline(sample, {"debug": True})
    print(result)
