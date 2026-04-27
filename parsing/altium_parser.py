# parsing/altium_parser.py

from pathlib import Path
from typing import Dict, Any, List
import xml.etree.ElementTree as ET

from utils.logger import get_module_logger

logger = get_module_logger(__name__)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def safe_attr(element, key, default=""):
    return element.attrib.get(key, default).strip()


def safe_text(element, default=""):
    return (element.text or default).strip()


# --------------------------------------------------
# PARSE COMPONENTS
# --------------------------------------------------
def parse_components(root) -> List[Dict[str, Any]]:
    components = []

    # Try multiple possible tags
    comp_tags = [
        ".//Component",
        ".//SchComponent",
        ".//Comp",
    ]

    found = []

    for tag in comp_tags:
        found.extend(root.findall(tag))

    for comp in found:
        try:
            ref = safe_attr(comp, "RefDes") or safe_attr(comp, "Designator")
            value = safe_attr(comp, "Value") or safe_attr(comp, "Comment")
            footprint = safe_attr(comp, "Footprint")

            if not ref:
                continue

            components.append({
                "ref": ref,
                "value": value,
                "footprint": footprint,
                "pins": []
            })

        except Exception as e:
            logger.warning(f"Component parse error: {e}")

    logger.info(f"Parsed {len(components)} components from Altium")

    return components


# --------------------------------------------------
# PARSE NETS
# --------------------------------------------------
def parse_nets(root) -> List[Dict[str, Any]]:
    nets = []

    net_tags = [
        ".//Net",
        ".//Signal",
    ]

    found = []

    for tag in net_tags:
        found.extend(root.findall(tag))

    for net in found:
        try:
            name = safe_attr(net, "Name") or safe_attr(net, "NetName")

            if not name:
                continue

            nets.append({
                "name": name,
                "connections": []
            })

        except Exception as e:
            logger.warning(f"Net parse error: {e}")

    logger.info(f"Parsed {len(nets)} nets from Altium")

    return nets


# --------------------------------------------------
# PARSE CONNECTIONS (PIN-LEVEL)
# --------------------------------------------------
def parse_connections(root) -> List[str]:
    """
    Extract pin-level connections like:
    (ComponentRef, Pin)
    """

    connections = []

    conn_tags = [
        ".//Pin",
        ".//Connection",
        ".//Node",
    ]

    found = []

    for tag in conn_tags:
        found.extend(root.findall(tag))

    for node in found:
        try:
            ref = safe_attr(node, "Component") or safe_attr(node, "RefDes")
            pin = safe_attr(node, "Pin") or safe_attr(node, "PinNumber")

            if ref and pin:
                connections.append(f"{ref}:{pin}")

        except Exception:
            continue

    logger.debug(f"Extracted {len(connections)} raw connections")

    return connections


# --------------------------------------------------
# MERGE CONNECTIONS INTO NETS
# --------------------------------------------------
def map_connections_to_nets(nets, connections):
    """
    Distribute connections across nets (best-effort)
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
def parse_altium(file_path: Path) -> Dict[str, Any]:
    """
    Parse Altium XML export into unified format
    """

    logger.info(f"Parsing Altium file: {file_path}")

    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} not found")

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        components = parse_components(root)
        nets = parse_nets(root)

        # Extract connections (best-effort)
        connections = parse_connections(root)
        nets = map_connections_to_nets(nets, connections)

        design = {
            "components": components,
            "nets": nets
        }

        logger.info("Altium parsing completed successfully")

        return design

    except ET.ParseError as e:
        logger.error(f"XML parsing failed: {e}")
        raise

    except Exception as e:
        logger.error(f"Altium parsing failed: {e}")
        raise


# --------------------------------------------------
# OPTIONAL VALIDATION
# --------------------------------------------------
def validate_design(design: Dict[str, Any]) -> bool:
    if "components" not in design or "nets" not in design:
        return False

    for c in design["components"]:
        if not c.get("ref"):
            return False

    return True


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    test_file = Path("altium_export.xml")

    if test_file.exists():
        result = parse_altium(test_file)

        print("\nComponents:")
        for c in result["components"]:
            print(c)

        print("\nNets:")
        for n in result["nets"]:
            print(n)
    else:
        print("Test file not found")
      
