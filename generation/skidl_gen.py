# generation/skidl_gen.py

from typing import Dict, Any
from pathlib import Path

from utils.logger import get_module_logger
from utils.output_manager import OutputManager
from config.settings import settings

logger = get_module_logger(__name__)
output_manager = OutputManager()


# --------------------------------------------------
# SAFE IMPORT SKIDL
# --------------------------------------------------
try:
    from skidl import Part, Net, generate_netlist, ERC, reset
    SKIDL_AVAILABLE = True
except ImportError:
    SKIDL_AVAILABLE = False
    logger.warning("SKiDL not installed. Install with: pip install skidl")


# --------------------------------------------------
# COMPONENT LIBRARY FALLBACK
# --------------------------------------------------
def safe_create_part(comp):
    """
    Safely create SKiDL part with fallback
    """
    value = comp.get("value", "R")
    footprint = comp.get("footprint", "")

    try:
        # Try using generic device lib
        part = Part("Device", value, footprint=footprint)
    except Exception:
        # Fallback to resistor
        part = Part("Device", "R")

    return part


# --------------------------------------------------
# BUILD PARTS
# --------------------------------------------------
def build_parts(design):
    parts = {}

    for comp in design.get("components", []):
        ref = comp["ref"]

        try:
            part = safe_create_part(comp)
            parts[ref] = part
        except Exception as e:
            logger.warning(f"Failed to create part {ref}: {e}")

    logger.info(f"Created {len(parts)} SKiDL parts")

    return parts


# --------------------------------------------------
# CONNECT NETS
# --------------------------------------------------
def connect_nets(design, parts):
    net_objects = {}

    for net in design.get("nets", []):
        net_name = net.get("name", "NET")

        try:
            skidl_net = Net(net_name)
            net_objects[net_name] = skidl_net

            for conn in net.get("connections", []):
                try:
                    ref, pin = conn.split(":")
                    if ref in parts:
                        skidl_net += parts[ref][pin]
                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"Net creation failed: {net_name} → {e}")

    logger.info(f"Connected {len(net_objects)} nets")

    return net_objects


# --------------------------------------------------
# GENERATE NETLIST
# --------------------------------------------------
def generate_skidl_netlist(design: Dict[str, Any]) -> Path:
    """
    Generate SKiDL netlist file
    """

    if not SKIDL_AVAILABLE:
        raise RuntimeError("SKiDL not installed")

    logger.info("Generating SKiDL netlist")

    reset()

    parts = build_parts(design)
    connect_nets(design, parts)

    try:
        ERC()  # Electrical Rule Check
    except Exception as e:
        logger.warning(f"ERC warnings: {e}")

    # Save netlist
    filename = output_manager.generate_filename("skidl_netlist", "net")
    output_path = settings.NETLIST_DIR / filename

    generate_netlist(file_=str(output_path))

    logger.info(f"Netlist generated at {output_path}")

    return output_path


# --------------------------------------------------
# OPTIONAL: GENERATE KICAD SCHEMATIC
# --------------------------------------------------
def export_kicad_schematic():
    """
    Uses KiCad CLI to convert netlist → schematic (if configured)
    """
    try:
        import os

        netlist_files = list(settings.NETLIST_DIR.glob("*.net"))
        if not netlist_files:
            logger.warning("No netlist found for schematic export")
            return None

        latest_netlist = max(netlist_files, key=lambda f: f.stat().st_mtime)

        output_file = settings.SCHEMATIC_DIR / "schematic.kicad_sch"

        cmd = f"{settings.KICAD_CLI} sch import netlist {latest_netlist} -o {output_file}"
        os.system(cmd)

        logger.info(f"Schematic exported to {output_file}")

        return output_file

    except Exception as e:
        logger.warning(f"KiCad export failed: {e}")
        return None


# --------------------------------------------------
# FULL PIPELINE WRAPPER
# --------------------------------------------------
def run_skidl_pipeline(design: Dict[str, Any]):
    """
    Full SKiDL flow:
    - Generate netlist
    - Optionally export schematic
    """

    result = {}

    try:
        netlist_path = generate_skidl_netlist(design)
        result["netlist"] = str(netlist_path)

        schematic_path = export_kicad_schematic()
        if schematic_path:
            result["schematic"] = str(schematic_path)

    except Exception as e:
        logger.error(f"SKiDL pipeline failed: {e}")

    return result


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample_design = {
        "components": [
            {"ref": "R1", "value": "10k", "footprint": "R_0805"},
            {"ref": "C1", "value": "100nF", "footprint": "C_0603"},
        ],
        "nets": [
            {"name": "NET1", "connections": ["R1:1", "C1:1"]},
            {"name": "GND", "connections": ["R1:2", "C1:2"]},
        ]
    }

    result = run_skidl_pipeline(sample_design)
    print(result)
  
