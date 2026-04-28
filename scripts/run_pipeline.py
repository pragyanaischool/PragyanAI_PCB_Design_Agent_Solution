# scripts/run_pipeline.py

from pathlib import Path

from parsing.router import parse_input
from normalization.normalize import normalize_design
from normalization.validator import validate_design

from generation.layout.auto_place import auto_place
from generation.routing.autorouter import autoroute

from generation.drc.checks import run_drc
from generation.autofix.fixer import auto_fix

from generation.render.pcb_plot import draw_pcb
from generation.render.svg_export import export_pcb_svg

from generation.export.bom import export_bom

from utils.logger import get_module_logger

logger = get_module_logger(__name__)


# --------------------------------------------------
# PIPELINE
# --------------------------------------------------
def run_pipeline(input_data):

    logger.info("🚀 Starting PCB Pipeline")

    # 1. Parse
    design = parse_input(input_data)

    # 2. Normalize
    design = normalize_design(design)

    # 3. Validate
    validate_design(design)

    # 4. Placement
    design = auto_place(design)

    # 5. Routing
    design = autoroute(design)

    # 6. DRC
    drc = run_drc(design)

    # 7. Auto-fix (if needed)
    if drc["status"] == "FAIL":
        design = auto_fix(design)

    # 8. Visualization
    draw_pcb(design)
    export_pcb_svg(design)

    # 9. Export
    export_bom(design)

    logger.info("✅ Pipeline completed")

    return design


# --------------------------------------------------
# RUN
# --------------------------------------------------
if __name__ == "__main__":

    # Example
    run_pipeline("data/sample.json")
