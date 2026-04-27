# simulation/ngspice.py

import subprocess
import tempfile
from pathlib import Path

from utils.logger import get_module_logger
from config.settings import settings

logger = get_module_logger(__name__)


# --------------------------------------------------
# GENERATE SIMPLE SPICE NETLIST
# --------------------------------------------------
def generate_spice_netlist(design: dict) -> str:
    """
    Convert design → SPICE netlist (basic)
    """

    lines = ["* Auto-generated SPICE Netlist"]

    node_map = {}
    node_id = 1

    def get_node(pin):
        nonlocal node_id
        if pin not in node_map:
            node_map[pin] = f"N{node_id}"
            node_id += 1
        return node_map[pin]

    # Components
    for comp in design.get("components", []):
        ref = comp["ref"]
        value = comp.get("value", "1k")

        # Find connections
        connected = []
        for net in design.get("nets", []):
            for conn in net.get("connections", []):
                if conn.startswith(ref):
                    connected.append(get_node(conn))

        if len(connected) >= 2:
            lines.append(f"{ref} {connected[0]} {connected[1]} {value}")

    # Basic analysis command
    lines.append(".op")
    lines.append(".end")

    return "\n".join(lines)


# --------------------------------------------------
# RUN NGSPICE
# --------------------------------------------------
def run_ngspice(netlist_str: str):
    """
    Run Ngspice simulation
    """

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".cir") as f:
            f.write(netlist_str.encode())
            netlist_path = f.name

        cmd = ["ngspice", "-b", netlist_path]

        result = subprocess.run(cmd, capture_output=True, text=True)

        logger.info("Ngspice simulation completed")

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }

    except FileNotFoundError:
        logger.warning("Ngspice not installed")
        return {"success": False, "error": "Ngspice not found"}

    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        return {"success": False, "error": str(e)}


# --------------------------------------------------
# PARSE OUTPUT
# --------------------------------------------------
def parse_ngspice_output(output: str):
    """
    Extract voltages/currents (basic parser)
    """

    results = {}

    for line in output.split("\n"):
        if "voltage" in line.lower():
            parts = line.split()
            if len(parts) >= 2:
                results[parts[0]] = parts[-1]

    return results


# --------------------------------------------------
# FULL PIPELINE
# --------------------------------------------------
def simulate(design: dict):
    netlist = generate_spice_netlist(design)

    result = run_ngspice(netlist)

    if result.get("success"):
        parsed = parse_ngspice_output(result.get("stdout", ""))
        return {
            "netlist": netlist,
            "raw": result,
            "parsed": parsed
        }

    return result


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample = {
        "components": [
            {"ref": "R1", "value": "1k"},
            {"ref": "R2", "value": "2k"},
        ],
        "nets": [
            {"name": "N1", "connections": ["R1:1", "R2:1"]},
            {"name": "GND", "connections": ["R1:2", "R2:2"]},
        ]
    }

    print(simulate(sample))
