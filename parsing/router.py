# parsing/router.py

from pathlib import Path
from typing import Dict, Any, Union, Tuple

from utils.logger import get_module_logger

# Import parsers
from parsing.csv_parser import parse_csv
from parsing.json_parser import parse_json
from parsing.kicad_parser import parse_kicad
from parsing.altium_parser import parse_altium
from parsing.net_extractor import extract_nets_from_file

logger = get_module_logger(__name__)


# --------------------------------------------------
# SUPPORTED FORMATS
# --------------------------------------------------
CSV_EXT = [".csv"]
JSON_EXT = [".json"]
KICAD_EXT = [".kicad_sch", ".sch"]
ALTIUM_EXT = [".xml"]


# --------------------------------------------------
# VALIDATION
# --------------------------------------------------
def validate_design(design: Dict[str, Any]) -> bool:
    """
    Ensure minimal valid structure
    """
    if not isinstance(design, dict):
        return False

    if "components" not in design or "nets" not in design:
        return False

    if not isinstance(design["components"], list):
        return False

    if not isinstance(design["nets"], list):
        return False

    return True


# --------------------------------------------------
# POST PROCESSING
# --------------------------------------------------
def enrich_with_nets_if_missing(design: Dict[str, Any], file_path: Path):
    """
    If nets are missing or empty → extract
    """
    if not design.get("nets"):
        logger.info("No nets found → extracting from file")

        try:
            nets = extract_nets_from_file(file_path)
            design["nets"] = nets
        except Exception as e:
            logger.warning(f"Net extraction failed: {e}")

    return design


# --------------------------------------------------
# MAIN ROUTER
# --------------------------------------------------
def parse_input(
    input_data: Union[str, Path, Tuple[Path, Path]]
) -> Dict[str, Any]:
    """
    Unified parsing entry point

    Supports:
    - CSV: (components.csv, nets.csv)
    - JSON: file.json
    - KiCad: file.kicad_sch
    - Altium: file.xml
    """

    logger.info("Starting input parsing")

    # --------------------------------------------------
    # CASE 1: CSV (two files)
    # --------------------------------------------------
    if isinstance(input_data, tuple):
        comp_file, net_file = input_data

        logger.info("Detected CSV input")

        design = parse_csv(comp_file, net_file)

        if not validate_design(design):
            raise ValueError("Invalid CSV design format")

        return design

    # --------------------------------------------------
    # CASE 2: SINGLE FILE
    # --------------------------------------------------
    file_path = Path(input_data)

    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} not found")

    suffix = file_path.suffix.lower()

    # ---------------- JSON ----------------
    if suffix in JSON_EXT:
        logger.info("Detected JSON input")

        design = parse_json(file_path)

    # ---------------- KICAD ----------------
    elif suffix in KICAD_EXT:
        logger.info("Detected KiCad schematic")

        design = parse_kicad(file_path)
        design = enrich_with_nets_if_missing(design, file_path)

    # ---------------- ALTIUM ----------------
    elif suffix in ALTIUM_EXT:
        logger.info("Detected Altium XML")

        design = parse_altium(file_path)
        design = enrich_with_nets_if_missing(design, file_path)

    else:
        raise ValueError(f"Unsupported file format: {suffix}")

    # --------------------------------------------------
    # FINAL VALIDATION
    # --------------------------------------------------
    if not validate_design(design):
        logger.error("Parsed design is invalid")
        raise ValueError("Invalid design structure")

    logger.info(
        f"Parsing completed: "
        f"{len(design['components'])} components, "
        f"{len(design['nets'])} nets"
    )

    return design


# --------------------------------------------------
# OPTIONAL: BATCH PARSER
# --------------------------------------------------
def parse_multiple(files: list) -> list:
    """
    Parse multiple inputs
    """

    results = []

    for f in files:
        try:
            results.append(parse_input(f))
        except Exception as e:
            logger.warning(f"Failed to parse {f}: {e}")

    return results


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":

    # Example usage

    # CSV
    # design = parse_input((Path("components.csv"), Path("nets.csv")))

    # JSON
    # design = parse_input("input.json")

    # KiCad
    # design = parse_input("design.kicad_sch")

    # Altium
    # design = parse_input("design.xml")

    print("Run with actual files to test parser")
