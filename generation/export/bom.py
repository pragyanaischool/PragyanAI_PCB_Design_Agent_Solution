# generation/export/bom.py

from pathlib import Path
from collections import defaultdict

from utils.logger import get_module_logger
from utils.output_manager import OutputManager

logger = get_module_logger(__name__)
output_manager = OutputManager()

# --------------------------------------------------
# GENERATE BOM DATA
# --------------------------------------------------
def generate_bom(design: dict):
    """
    Group components by value + footprint
    """

    grouped = defaultdict(list)

    for comp in design.get("components", []):
        key = (
            comp.get("value", "UNKNOWN"),
            comp.get("footprint", "UNKNOWN")
        )

        grouped[key].append(comp.get("ref"))

    bom = []

    for (value, footprint), refs in grouped.items():
        bom.append({
            "value": value,
            "footprint": footprint,
            "quantity": len(refs),
            "refs": refs
        })

    return bom


# --------------------------------------------------
# EXPORT BOM (CSV)
# --------------------------------------------------
def export_bom_csv(design: dict) -> Path:
    bom = generate_bom(design)

    filename = output_manager.generate_filename("bom", "csv")
    path = output_manager.dirs["pcbs"] / filename

    with open(path, "w") as f:
        f.write("Value,Footprint,Quantity,Refs\n")

        for item in bom:
            f.write(
                f"{item['value']},"
                f"{item['footprint']},"
                f"{item['quantity']},"
                f"{' '.join(item['refs'])}\n"
            )

    logger.info(f"BOM CSV exported: {path}")

    return path


# --------------------------------------------------
# EXPORT BOM (JSON)
# --------------------------------------------------
def export_bom_json(design: dict) -> Path:
    import json

    bom = generate_bom(design)

    filename = output_manager.generate_filename("bom", "json")
    path = output_manager.dirs["pcbs"] / filename

    with open(path, "w") as f:
        json.dump(bom, f, indent=2)

    logger.info(f"BOM JSON exported: {path}")

    return path


# --------------------------------------------------
# FULL BOM EXPORT
# --------------------------------------------------
def export_bom(design: dict):
    return {
        "csv": str(export_bom_csv(design)),
        "json": str(export_bom_json(design))
    }
  
