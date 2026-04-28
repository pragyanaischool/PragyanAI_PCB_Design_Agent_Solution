# normalization/validator.py

from typing import Dict, Any, List, Set, Tuple
from utils.logger import get_module_logger

logger = get_module_logger(__name__)


# --------------------------------------------------
# ERROR STRUCTURE
# --------------------------------------------------
def make_error(msg, type_="ERROR", details=None):
    return {
        "type": type_,
        "message": msg,
        "details": details or {}
    }


# --------------------------------------------------
# BASIC STRUCTURE VALIDATION
# --------------------------------------------------
def validate_structure(design: Dict[str, Any]) -> List[Dict]:
    errors = []

    if "components" not in design:
        errors.append(make_error("Missing components"))

    if "nets" not in design:
        errors.append(make_error("Missing nets"))

    if not isinstance(design.get("components", []), list):
        errors.append(make_error("Components must be a list"))

    if not isinstance(design.get("nets", []), list):
        errors.append(make_error("Nets must be a list"))

    return errors


# --------------------------------------------------
# COMPONENT VALIDATION
# --------------------------------------------------
def validate_components(design: Dict[str, Any]) -> Tuple[List[Dict], Set[str]]:
    errors = []
    refs = set()

    for comp in design.get("components", []):
        ref = comp.get("ref")

        if not ref:
            errors.append(make_error("Component missing ref", details=comp))
            continue

        if ref in refs:
            errors.append(make_error(f"Duplicate component: {ref}"))

        refs.add(ref)

    return errors, refs


# --------------------------------------------------
# NET VALIDATION
# --------------------------------------------------
def validate_nets(design: Dict[str, Any], refs: Set[str]) -> List[Dict]:
    errors = []

    for net in design.get("nets", []):
        name = net.get("name")

        if not name:
            errors.append(make_error("Net missing name", details=net))
            continue

        conns = net.get("connections", [])

        if len(conns) < 2:
            errors.append(make_error(
                f"Weak net: {name}",
                "WARNING",
                {"connections": conns}
            ))

        for conn in conns:
            if ":" not in conn:
                errors.append(make_error(
                    f"Invalid connection format: {conn}",
                    details={"net": name}
                ))
                continue

            ref, _ = conn.split(":", 1)

            if ref not in refs:
                errors.append(make_error(
                    f"Unknown component in net: {ref}",
                    details={"net": name}
                ))

    return errors


# --------------------------------------------------
# LAYOUT VALIDATION
# --------------------------------------------------
def validate_layout(design: Dict[str, Any], refs: Set[str]) -> List[Dict]:
    errors = []
    layout = design.get("layout", {})

    for ref, pos in layout.items():
        if ref not in refs:
            errors.append(make_error(
                f"Layout references unknown component: {ref}"
            ))

        if not isinstance(pos, dict):
            errors.append(make_error(f"Invalid layout for {ref}"))
            continue

        if "x" not in pos or "y" not in pos:
            errors.append(make_error(f"Missing coordinates for {ref}"))

    return errors


# --------------------------------------------------
# ROUTING VALIDATION
# --------------------------------------------------
def validate_routes(design: Dict[str, Any]) -> List[Dict]:
    errors = []

    nets = {n["name"] for n in design.get("nets", [])}

    for route in design.get("routes", []):
        net = route.get("net")

        if net not in nets:
            errors.append(make_error(
                f"Route references unknown net: {net}"
            ))

        path = route.get("path", [])

        if not isinstance(path, list) or len(path) < 2:
            errors.append(make_error(
                f"Invalid route path for net {net}"
            ))

    return errors


# --------------------------------------------------
# CONNECTIVITY VALIDATION
# --------------------------------------------------
def validate_connectivity(design: Dict[str, Any]) -> List[Dict]:
    """
    Check if all components are connected to at least one net
    """
    errors = []

    connected = set()

    for net in design.get("nets", []):
        for conn in net.get("connections", []):
            ref = conn.split(":")[0]
            connected.add(ref)

    for comp in design.get("components", []):
        if comp["ref"] not in connected:
            errors.append(make_error(
                f"Unconnected component: {comp['ref']}",
                "WARNING"
            ))

    return errors


# --------------------------------------------------
# MAIN VALIDATOR
# --------------------------------------------------
def validate_design(
    design: Dict[str, Any],
    strict: bool = False
) -> Dict[str, Any]:
    """
    Full validation pipeline
    """

    logger.info("Starting design validation")

    errors = []

    # 1. Structure
    errors.extend(validate_structure(design))

    # 2. Components
    comp_errors, refs = validate_components(design)
    errors.extend(comp_errors)

    # 3. Nets
    errors.extend(validate_nets(design, refs))

    # 4. Layout
    errors.extend(validate_layout(design, refs))

    # 5. Routes
    errors.extend(validate_routes(design))

    # 6. Connectivity
    errors.extend(validate_connectivity(design))

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------
    error_count = len([e for e in errors if e["type"] == "ERROR"])
    warning_count = len([e for e in errors if e["type"] == "WARNING"])

    status = "PASS" if error_count == 0 else "FAIL"

    result = {
        "status": status,
        "errors": errors,
        "total_errors": error_count,
        "total_warnings": warning_count
    }

    logger.info(
        f"Validation complete → {error_count} errors, {warning_count} warnings"
    )

    if strict and error_count > 0:
        raise ValueError("Validation failed with errors")

    return result


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample = {
        "components": [
            {"ref": "R1"},
            {"ref": "R1"},  # duplicate
        ],
        "nets": [
            {"name": "VCC", "connections": ["R1:1", "U1:1"]},  # U1 missing
        ],
        "layout": {
            "R1": {"x": 10},
        },
        "routes": [
            {"net": "UNKNOWN", "path": [(0, 0)]},
        ]
    }

    result = validate_design(sample)

    from pprint import pprint
    pprint(result)
  
