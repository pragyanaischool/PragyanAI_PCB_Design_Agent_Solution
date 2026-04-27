# parsing/net_extractor.py

from pathlib import Path
from typing import Dict, Any, List
import re
from collections import defaultdict

from utils.logger import get_module_logger

logger = get_module_logger(__name__)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def extract_ref_pin(token: str):
    """
    Convert 'U1:VCC' → ('U1', 'VCC')
    """
    try:
        ref, pin = token.split(":")
        return ref.strip(), pin.strip()
    except:
        return None, None


def normalize_connection(conn: str) -> str:
    """
    Normalize connection string
    """
    return conn.strip().replace(" ", "")


# --------------------------------------------------
# KICAD NET EXTRACTION (IMPROVED)
# --------------------------------------------------
def extract_kicad_nets(content: str) -> List[Dict[str, Any]]:
    """
    Extract nets from KiCad schematic content
    """

    nets = []

    # Match: (net (code X) (name "VCC"))
    matches = re.findall(
        r'\(net\s+\(code\s+\d+\)\s+\(name\s+"(.*?)"\)\)',
        content
    )

    for name in matches:
        nets.append({
            "name": name,
            "connections": []
        })

    logger.info(f"Extracted {len(nets)} KiCad nets")

    return nets


# --------------------------------------------------
# CONNECTION EXTRACTION
# --------------------------------------------------
def extract_connections(content: str) -> List[str]:
    """
    Extract connection patterns from text
    Supports:
    - (connect (ref U1) (pin 1))
    - U1:1 patterns
    """

    connections = []

    # Pattern 1: KiCad style
    matches = re.findall(
        r'\(connect\s+\(ref\s+(.*?)\)\s+\(pin\s+(.*?)\)\)',
        content
    )

    for ref, pin in matches:
        connections.append(f"{ref}:{pin}")

    # Pattern 2: Direct ref:pin
    matches2 = re.findall(r'([A-Za-z]+\d+:\w+)', content)

    for m in matches2:
        connections.append(m)

    connections = list(set(connections))  # remove duplicates

    logger.debug(f"Extracted {len(connections)} connections")

    return connections


# --------------------------------------------------
# GROUP CONNECTIONS INTO NETS
# --------------------------------------------------
def group_connections(connections: List[str]) -> List[Dict[str, Any]]:
    """
    Build nets from connections using simple grouping
    """

    nets = []
    visited = set()

    for conn in connections:
        if conn in visited:
            continue

        group = [conn]
        visited.add(conn)

        ref1, _ = extract_ref_pin(conn)

        for other in connections:
            if other in visited:
                continue

            ref2, _ = extract_ref_pin(other)

            # simple grouping rule: same component
            if ref1 == ref2:
                group.append(other)
                visited.add(other)

        nets.append({
            "name": f"NET_{len(nets)+1}",
            "connections": group
        })

    return nets


# --------------------------------------------------
# MERGE NETS
# --------------------------------------------------
def merge_nets(existing: List[Dict], new: List[Dict]) -> List[Dict]:
    """
    Merge nets intelligently
    """

    net_map = {n["name"]: n for n in existing}

    for net in new:
        name = net["name"]

        if name in net_map:
            net_map[name]["connections"].extend(net["connections"])
        else:
            net_map[name] = net

    # Remove duplicates
    for net in net_map.values():
        net["connections"] = list(set(net["connections"]))

    return list(net_map.values())


# --------------------------------------------------
# MAIN FILE-BASED EXTRACTION
# --------------------------------------------------
def extract_nets_from_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Auto-detect and extract nets from file
    """

    logger.info(f"Extracting nets from: {file_path}")

    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} not found")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    nets = []
    connections = extract_connections(content)

    # KiCad-specific
    if file_path.suffix in [".kicad_sch", ".sch"]:
        nets = extract_kicad_nets(content)

        if nets:
            # distribute connections
            for i, conn in enumerate(connections):
                nets[i % len(nets)]["connections"].append(conn)
        else:
            nets = group_connections(connections)

    else:
        nets = group_connections(connections)

    logger.info(f"Final nets: {len(nets)}")

    return nets


# --------------------------------------------------
# ENRICH DESIGN
# --------------------------------------------------
def enrich_design_with_nets(design: Dict[str, Any], nets: List[Dict]) -> Dict[str, Any]:
    """
    Add nets to design safely
    """

    existing = design.get("nets", [])

    merged = merge_nets(existing, nets)

    design["nets"] = merged

    return design


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    test_file = Path("sample.kicad_sch")

    if test_file.exists():
        nets = extract_nets_from_file(test_file)

        for n in nets:
            print(n)
    else:
        print("Test file not found")
      
