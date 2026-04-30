# orchestration/agents/render_agent.py

from typing import Dict, Any
from pathlib import Path

# Optional render backends
try:
    from generation.render.pcb_plot import plot_pcb
    PLOT_AVAILABLE = True
except Exception:
    PLOT_AVAILABLE = False

try:
    from generation.render.svg_export import export_svg
    SVG_AVAILABLE = True
except Exception:
    SVG_AVAILABLE = False

try:
    from generation.render.schematic_plot import plot_schematic
    SCHEMATIC_AVAILABLE = True
except Exception:
    SCHEMATIC_AVAILABLE = False


# ==================================================
# OUTPUT PATHS
# ==================================================
OUTPUT_DIR = Path("outputs/images")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ==================================================
# SAVE IMAGE (WRAPPER)
# ==================================================
def _render_image(design: Dict[str, Any], filename: str):
    """
    Render PCB layout image
    """
    if not PLOT_AVAILABLE:
        return None

    path = OUTPUT_DIR / filename

    try:
        plot_pcb(design, save_path=str(path))
        return path
    except Exception:
        return None


# ==================================================
# EXPORT SVG
# ==================================================
def _render_svg(design: Dict[str, Any], filename: str):
    if not SVG_AVAILABLE:
        return None

    path = OUTPUT_DIR / filename

    try:
        export_svg(design, str(path))
        return path
    except Exception:
        return None


# ==================================================
# SCHEMATIC PREVIEW
# ==================================================
def _render_schematic(design: Dict[str, Any], filename: str):
    if not SCHEMATIC_AVAILABLE:
        return None

    path = OUTPUT_DIR / filename

    try:
        plot_schematic(design, save_path=str(path))
        return path
    except Exception:
        return None


# ==================================================
# MAIN AGENT
# ==================================================
def run_render(state):
    """
    Render Agent:
    - Generates PCB visualization
    - Saves outputs (PNG, SVG, schematic)
    """

    try:
        state.set_stage("render")
        state.log("Rendering started")

        design = state.get_design()

        if not design:
            raise ValueError("No design available for rendering")

        outputs = {}

        # --------------------------------------------------
        # PCB IMAGE (PNG)
        # --------------------------------------------------
        img_path = _render_image(design, "pcb_layout.png")

        if img_path:
            outputs["image"] = str(img_path)
            state.log(f"PCB image saved: {img_path}")
        else:
            state.log("PCB image rendering unavailable", level="WARNING")

        # --------------------------------------------------
        # SVG EXPORT
        # --------------------------------------------------
        svg_path = _render_svg(design, "pcb_layout.svg")

        if svg_path:
            outputs["svg"] = str(svg_path)
            state.log(f"SVG exported: {svg_path}")
        else:
            state.log("SVG export unavailable", level="WARNING")

        # --------------------------------------------------
        # SCHEMATIC IMAGE
        # --------------------------------------------------
        sch_path = _render_schematic(design, "schematic.png")

        if sch_path:
            outputs["schematic"] = str(sch_path)
            state.log(f"Schematic rendered: {sch_path}")
        else:
            state.log("Schematic rendering unavailable", level="WARNING")

        # --------------------------------------------------
        # UPDATE STATE
        # --------------------------------------------------
        state["render_outputs"] = outputs
        state["render_done"] = True

        # Snapshot
        state.snapshot("render")

        state.log("Rendering completed")

    except Exception as e:
        state.add_error(f"Render failed: {str(e)}")
        state.log("Render error occurred", level="ERROR")
