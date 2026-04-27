# parsing/kicad_parser.py

from pathlib import Path
from typing import Dict, Any, List
import re

from utils.logger import get_module_logger

logger = get_module_logger(__name__)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def extract_property(block: str, prop_name: str) -> str:
    """
    Extract property value from symbol block
    """
    match = re.search(rf'\(property "{prop_name}" "(.*?)"\)', block)
    return match.group(1) if match else ""


def extract_symbol_blocks(content: str) -> List[str]:
    """
    Extract (symbol ...) blocks
    """
    return re.findall(r"\(symbol\s.*?\)\s*\)", content, re.DOTALL)


def extract_net_blocks(content: str) -> List[str]:
    """
    Extract (net ...) blocks
    """
    return re.findall(r"\(net\s+.*?\)", content, re.DOTALL)


# --------------------------------------------------
# PARSE COMPONENTS
# --------------------------------------------------
def parse_components(content: str) -> List[Dict[str, Any]]:
    components = []

    symbol_blocks = extract_symbol_blocks(content)

    for block in symbol_blocks:
        try:
            ref = extract_property(block, "Reference")
            value = extract_property(block, "Value")
            footprint = extract_property(block, "Footprint")

            if not ref:
                continue

            comp = {
                "ref": ref,
                "value": value,
                "footprint": footprint,
                "pins": []  # filled later if needed
            }

            components.append(comp)

        except Exception as e:
            logger.warning(f"Failed to parse symbol block: {e}")

    logger.info(f"Parsed {len(components)} components from KiCad")

    return components


# --------------------------------------------------
# PARSE NETS (BASIC)
# --------------------------------------------------
def parse_nets(content: str) -> List[Dict[str, Any]]:
    """
    Basic net extraction (not full connectivity graph)
    """

    nets = []

    try:
        net_blocks = extract_net_blocks(content)

        for block in net_blocks:
            name_match = re.search(r'"(.*?)"', block)

            if name_match:
                nets.append({
                    "name": name_match.group(1),
                    "connections": []  # detailed extraction is complex
                })

    except Exception as e:
        logger.warning(f"Net parsing failed: {e}")

    logger.info(f"Parsed {len(nets)} nets from KiCad")

    return nets


# --------------------------------------------------
# ADVANCED: CONNECTION EXTRACTION (BEST EFFORT)
# --------------------------------------------------
def extract_connections(content: str) -> List[Dict[str, Any]]:
    """
    Extract connections like:
    (connect (ref U1) (pin 1))
    """

    connections = []

    try:
        matches = re.findall(
            r'\(connect\s+\(ref\s+(.*?)\)\s+\(pin\s+(.*?)\)\)',
            content
        )

        for ref, pin in matches:
            connections.append(f"{ref}:{pin}")

    except Exception as e:
        logger.debug(f"Connection extraction failed: {e}")

    return connections


# --------------------------------------------------
# MERGE CONNECTIONS INTO NETS (BEST EFFORT)
# --------------------------------------------------
def enrich_nets_with_connections(nets, connections):
    """
    Distribute connections (simplified)
    """
    if not nets:
        return nets

    idx = 0
    for conn in connections:
        nets[idx % len(nets)]["connections"].append(conn)
        idx += 1

    return nets


# --------------------------------------------------
# MAIN PARSER
# --------------------------------------------------
def parse_kicad(file_path: Path) -> Dict[str, Any]:
    """
    Parse KiCad schematic file into unified format
    """

    logger.info(f"Parsing KiCad file: {file_path}")

    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} not found")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        components = parse_components(content)
        nets = parse_nets(content)

        # Try extracting connections (best-effort)
        connections = extract_connections(content)
        nets = enrich_nets_with_connections(nets, connections)

        design = {
            "components": components,
            "nets": nets
        }

        logger.info("KiCad parsing completed successfully")

        return design

    except Exception as e:
        logger.error(f"KiCad parsing failed: {e}")
        raise


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    test_file = Path("sample.kicad_sch")

    if test_file.exists():
        result = parse_kicad(test_file)

        print("\nComponents:")
        for c in result["components"]:
            print(c)

        print("\nNets:")
        for n in result["nets"]:
            print(n)
    else:
        print("Test file not found")
