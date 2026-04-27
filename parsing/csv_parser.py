# parsing/csv_parser.py

import csv
from pathlib import Path
from typing import Dict, List, Any

from utils.logger import get_module_logger

logger = get_module_logger(__name__)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def clean_list_field(value: str) -> List[str]:
    """
    Convert CSV string like "A,B,C" → ["A","B","C"]
    Handles quotes, spaces, empty values
    """
    if not value:
        return []

    value = value.strip().replace('"', '')
    return [v.strip() for v in value.split(",") if v.strip()]


def validate_component(row: Dict[str, Any]) -> bool:
    return "ref" in row and row["ref"]


def validate_net(row: Dict[str, Any]) -> bool:
    return "net" in row and row["net"]


# --------------------------------------------------
# PARSE COMPONENTS CSV
# --------------------------------------------------
def parse_components_csv(file_path: Path) -> List[Dict[str, Any]]:
    components = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for i, row in enumerate(reader, start=1):

                if not validate_component(row):
                    logger.warning(f"Skipping invalid component row {i}")
                    continue

                component = {
                    "ref": row.get("ref").strip(),
                    "value": row.get("value", "").strip(),
                    "footprint": row.get("footprint", "").strip(),
                    "pins": clean_list_field(row.get("pins", ""))
                }

                components.append(component)

        logger.info(f"Parsed {len(components)} components")

    except Exception as e:
        logger.error(f"Failed to parse components CSV: {e}")
        raise

    return components


# --------------------------------------------------
# PARSE NETS CSV
# --------------------------------------------------
def parse_nets_csv(file_path: Path) -> List[Dict[str, Any]]:
    nets = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for i, row in enumerate(reader, start=1):

                if not validate_net(row):
                    logger.warning(f"Skipping invalid net row {i}")
                    continue

                net = {
                    "name": row.get("net").strip(),
                    "connections": clean_list_field(row.get("connections", ""))
                }

                nets.append(net)

        logger.info(f"Parsed {len(nets)} nets")

    except Exception as e:
        logger.error(f"Failed to parse nets CSV: {e}")
        raise

    return nets


# --------------------------------------------------
# MAIN CSV PARSER
# --------------------------------------------------
def parse_csv(
    components_file: Path,
    nets_file: Path
) -> Dict[str, Any]:
    """
    Parse CSV files into unified design format

    Returns:
    {
        "components": [...],
        "nets": [...]
    }
    """

    logger.info("Starting CSV parsing")

    if not components_file.exists():
        raise FileNotFoundError(f"{components_file} not found")

    if not nets_file.exists():
        raise FileNotFoundError(f"{nets_file} not found")

    components = parse_components_csv(components_file)
    nets = parse_nets_csv(nets_file)

    design = {
        "components": components,
        "nets": nets
    }

    logger.info("CSV parsing completed successfully")

    return design


# --------------------------------------------------
# OPTIONAL: VALIDATE DESIGN STRUCTURE
# --------------------------------------------------
def validate_design(design: Dict[str, Any]) -> bool:
    """
    Basic schema validation
    """

    if "components" not in design or "nets" not in design:
        return False

    for comp in design["components"]:
        if "ref" not in comp:
            return False

    for net in design["nets"]:
        if "name" not in net:
            return False

    return True


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    comp_file = Path("components.csv")
    net_file = Path("nets.csv")

    design = parse_csv(comp_file, net_file)

    print("\nParsed Design:")
    for comp in design["components"]:
        print(comp)

    for net in design["nets"]:
        print(net)
      
