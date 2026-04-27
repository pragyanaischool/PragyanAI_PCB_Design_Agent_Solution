# generation/export/gerber.py

from pathlib import Path

from utils.logger import get_module_logger
from utils.output_manager import OutputManager

logger = get_module_logger(__name__)
output_manager = OutputManager()

# --------------------------------------------------
# GENERATE GERBER CONTENT
# --------------------------------------------------
def generate_gerber_content(design: dict) -> str:
    content = "G04 Gerber File*\n"
    content += "%FSLAX24Y24*%\n"

    for route in design.get("routes", []):
        for x, y in route.get("path", []):
            content += f"X{x}Y{y}D01*\n"

    content += "M02*\n"

    return content


# --------------------------------------------------
# SAVE GERBER FILE
# --------------------------------------------------
def export_gerber(design: dict) -> Path:
    content = generate_gerber_content(design)

    filename = output_manager.generate_filename("gerber", "gbr")
    path = output_manager.dirs["gerbers"] / filename

    with open(path, "w") as f:
        f.write(content)

    logger.info(f"Gerber file generated: {path}")

    return path


# --------------------------------------------------
# MULTI-LAYER GERBER (FUTURE READY)
# --------------------------------------------------
def export_gerber_layers(design: dict):
    files = {}

    for layer in ["top", "bottom"]:
        filename = output_manager.generate_filename(f"gerber_{layer}", "gbr")
        path = output_manager.dirs["gerbers"] / filename

        with open(path, "w") as f:
            f.write(generate_gerber_content(design))

        files[layer] = str(path)

    return files
