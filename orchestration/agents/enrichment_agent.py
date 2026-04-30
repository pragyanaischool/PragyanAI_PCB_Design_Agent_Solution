# orchestration/agents/enrichment_agent.py

from typing import Dict, Any, List

from enrichment.pin_mapping import map_pins
from enrichment.footprint_resolution import resolve_footprints
from enrichment.hierarchy import flatten_hierarchy
from enrichment.rules_engine import apply_rules


# ==================================================
# VALIDATION HELPERS
# ==================================================
def _validate_enrichment(components: List[Dict[str, Any]]) -> List[str]:
    """
    Ensure components have required enriched fields
    """
    errors = []

    for c in components:
        ref = c.get("ref", "UNKNOWN")

        if not c.get("pins"):
            errors.append(f"{ref}: Missing pins")

        if not c.get("footprint"):
            errors.append(f"{ref}: Missing footprint")

    return errors


def _safe_map_pins(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    try:
        return map_pins(components)
    except Exception:
        # Fallback: keep original components
        return components


def _safe_resolve_footprints(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    try:
        return resolve_footprints(components)
    except Exception:
        return components


# ==================================================
# MAIN AGENT
# ==================================================
def run_enrichment(state):
    """
    Enrichment Agent:
    - Adds pin mappings
    - Resolves footprints
    - Applies design rules
    - Handles hierarchy
    """

    try:
        state.set_stage("enrichment")
        state.log("Enrichment started")

        design = state.get_design()

        if not design:
            raise ValueError("No design available for enrichment")

        # --------------------------------------------------
        # HIERARCHY (multi-sheet support)
        # --------------------------------------------------
        try:
            design = flatten_hierarchy(design)
            state.log("Hierarchy flattened")
        except Exception:
            state.log("Hierarchy flatten failed (skipped)", level="WARNING")

        # --------------------------------------------------
        # PIN MAPPING
        # --------------------------------------------------
        components = design.get("components", [])
        components = _safe_map_pins(components)

        # --------------------------------------------------
        # FOOTPRINT RESOLUTION
        # --------------------------------------------------
        components = _safe_resolve_footprints(components)

        design["components"] = components

        # --------------------------------------------------
        # RULE APPLICATION
        # --------------------------------------------------
        try:
            design = apply_rules(design)
            state.log("Rules applied")
        except Exception:
            state.log("Rule engine failed (skipped)", level="WARNING")

        # --------------------------------------------------
        # VALIDATION
        # --------------------------------------------------
        errors = _validate_enrichment(components)

        if errors:
            state.log(f"Enrichment warnings: {errors}", level="WARNING")

        # --------------------------------------------------
        # UPDATE STATE
        # --------------------------------------------------
        state.update_design(design)
        state["enriched"] = True

        # Snapshot
        state.snapshot("enriched")

        # Logging summary
        comps = len(components)
        state.log(f"Enrichment complete: {comps} components enriched")

    except Exception as e:
        state.add_error(f"Enrichment failed: {str(e)}")
        state.log("Enrichment error occurred", level="ERROR")
      
