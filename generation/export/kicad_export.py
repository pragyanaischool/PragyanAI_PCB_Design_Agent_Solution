# generation/export/kicad_export.py
import os
from pathlib import Path

from config.settings import settings
from utils.logger import get_module_logger
from utils.output_manager import OutputManager

logger = get_module_logger(__name__)
output_manager = OutputManager()

# --------------------------------------------------
# EXPORT NETLIST → KICAD SCHEMATIC
# --------------------------------------------------
def export_schematic(netlist_path: Path) -> Path:
    """
    Convert netlist → KiCad schematic (CLI-based)
    """

    if not netlist_path.exists():
        logger.error("Netlist not found")
        return None

    output_file = settings.SCHEMATIC_DIR / "design.kicad_sch"

    cmd = f"{settings.KICAD_CLI} sch import netlist {netlist_path} -o {output_file}"

    os.system(cmd)

    logger.info(f"Schematic exported: {output_file}")

    return output_file

# --------------------------------------------------
# EXPORT PCB (SIMULATED)
# --------------------------------------------------
def export_pcb(design: dict) -> Path:
    """
    Save PCB layout as JSON (placeholder for real KiCad PCB)
    """

    filename = output_manager.generate_filename("pcb_layout", "kicad_pcb")
    path = settings.PCB_DIR / filename

    with open(path, "w") as f:
        f.write(str(design))

    logger.info(f"PCB exported: {path}")

    return path

# --------------------------------------------------
# FULL EXPORT PIPELINE
# --------------------------------------------------
def export_kicad(design: dict, netlist_path: Path = None):
    result = {}

    if netlist_path:
        result["schematic"] = str(export_schematic(netlist_path))

    result["pcb"] = str(export_pcb(design))

    return result
  
