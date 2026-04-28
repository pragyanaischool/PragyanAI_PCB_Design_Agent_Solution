# normalization/normalize.py

from typing import Dict, Any, List, Tuple
from copy import deepcopy

from normalization.schema import Design, Component, Net, Route, Placement
from utils.logger import get_module_logger
from config.settings import settings

logger = get_module_logger(__name__)


# --------------------------------------------------
# CONFIG
# --------------------------------------------------
GRID = getattr(settings, "GRID_SIZE", 1)
BOARD_W = getattr(settings, "BOARD_WIDTH", 200)
BOARD_H = getattr(settings, "BOARD_HEIGHT", 150)


# --------------------------------------------------
# STRING HELPERS
# --------------------------------------------------
def _norm_str(v: Any) -> str:
    return str(v or "").strip()


def _norm_upper(v: Any) -> str:
    return _norm_str(v).upper()


def _unique_list(seq: List[str]) -> List[str]:
    return list(dict.fromkeys(seq))  # preserves order


# --------------------------------------------------
# CONNECTION HELPERS
# --------------------------------------------------
def _normalize_connection(conn: str) -> str:
    """
    Normalize 'u1 : vcc ' -> 'U1:VCC'
    """
    if not conn or ":" not in conn:
        return ""
    ref, pin = conn.split(":", 1)
    return f"{_norm_upper(ref)}:{_norm_upper(pin)}"


def _filter_connections(conns: List[str]) -> List[str]:
    """
    - normalize
    - remove invalid
    - deduplicate
    """
    out = []
    for c in conns or []:
        nc = _normalize_connection(c)
        if nc and ":" in nc:
            out.append(nc)
    return _unique_list(out)


# --------------------------------------------------
# COMPONENT NORMALIZATION
# --------------------------------------------------
def _normalize_components(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    norm = []

    for c in components or []:
        ref = _norm_upper(c.get("ref"))
        if not ref:
            continue

        comp = {
            "ref": ref,
            "value": _norm_str(c.get("value")),
            "footprint": _norm_str(c.get("footprint")),
            "pins": [],
            "metadata": c.get("metadata", {}) or {}
        }

        # pins can be list or string
        pins = c.get("pins", [])
        if isinstance(pins, str):
            pins = [p.strip() for p in pins.split(",") if p.strip()]

        comp["pins"] = [_norm_upper(p) for p in pins]

        norm.append(comp)

    # deterministic order
    norm.sort(key=lambda x: x["ref"])
    return norm


# --------------------------------------------------
# NET NORMALIZATION
# --------------------------------------------------
def _normalize_nets(nets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    norm = []

    for n in nets or []:
        name = _norm_upper(n.get("name") or n.get("net"))
        if not name:
            continue

        conns = _filter_connections(n.get("connections", []))

        # remove self duplicates like U1:1 appearing twice
        conns = _unique_list(conns)

        norm.append({
            "name": name,
            "connections": conns,
            "metadata": n.get("metadata", {}) or {}
        })

    # deterministic order
    norm.sort(key=lambda x: x["name"])
    return norm


# --------------------------------------------------
# LAYOUT NORMALIZATION
# --------------------------------------------------
def _snap(v: float) -> float:
    if GRID <= 0:
        return v
    return round(v / GRID) * GRID


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(x, hi))


def _normalize_layout(layout: Dict[str, Any]) -> Dict[str, Any]:
    """
    - snap to grid
    - clamp to board
    - ensure numeric
    """
    norm = {}

    for ref, pos in (layout or {}).items():
        try:
            x = float(pos.get("x", 0))
            y = float(pos.get("y", 0))
            rot = float(pos.get("rotation", 0.0))
            layer = pos.get("layer", "top")

            x = _clamp(_snap(x), 0, BOARD_W)
            y = _clamp(_snap(y), 0, BOARD_H)

            norm[_norm_upper(ref)] = {
                "x": x,
                "y": y,
                "rotation": rot,
                "layer": layer
            }
        except Exception:
            continue

    return norm


# --------------------------------------------------
# ROUTE NORMALIZATION
# --------------------------------------------------
def _normalize_path(path: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    out = []
    for p in path or []:
        try:
            x, y = float(p[0]), float(p[1])
            out.append((_snap(x), _snap(y)))
        except Exception:
            continue
    return out


def _normalize_routes(routes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    norm = []

    for r in routes or []:
        net = _norm_upper(r.get("net"))
        if not net:
            continue

        route = {
            "net": net,
            "path": _normalize_path(r.get("path", [])),
            "width": float(r.get("width", getattr(settings, "MIN_TRACE_WIDTH", 0.2))),
            "layer": r.get("layer", "top"),
            "metadata": r.get("metadata", {}) or {}
        }

        norm.append(route)

    return norm


# --------------------------------------------------
# OPTIONAL ENRICHMENT HOOKS
# --------------------------------------------------
def _resolve_footprints(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Placeholder: map value/package -> footprint
    """
    # Example heuristic (extend as needed)
    for c in components:
        if not c["footprint"]:
            val = c.get("value", "").lower()
            if "res" in val or "k" in val:
                c["footprint"] = "Resistor_SMD:R_0805"
            elif "nf" in val or "pf" in val:
                c["footprint"] = "Capacitor_SMD:C_0603"
    return components


def _pin_mapping(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Placeholder: map symbolic pins if missing
    """
    # Keep as hook for future symbol libraries
    return components


# --------------------------------------------------
# MAIN NORMALIZER
# --------------------------------------------------
def normalize_design(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Full normalization pipeline:
      - sanitize raw dict
      - normalize components, nets, layout, routes
      - optional enrichment (pins, footprints)
      - validate via Pydantic schema
      - return canonical dict
    """

    logger.info("Normalization: start")

    if not isinstance(raw, dict):
        raise ValueError("Input must be a dict")

    data = deepcopy(raw)

    # 1) Core fields
    components = _normalize_components(data.get("components", []))
    nets = _normalize_nets(data.get("nets", []))

    # 2) Optional enrichment
    components = _resolve_footprints(components)
    components = _pin_mapping(components)

    # 3) Layout / Routes
    layout = _normalize_layout(data.get("layout", {}))
    routes = _normalize_routes(data.get("routes", []))

    # 4) Assemble
    assembled = {
        "components": components,
        "nets": nets,
        "layout": layout,
        "routes": routes,
        "constraints": data.get("constraints", {}) or {},
        "metadata": data.get("metadata", {}) or {},
    }

    # 5) Validate with schema (coercion + strict checks)
    try:
        design_obj = Design(**assembled)
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        raise

    clean = design_obj.dict()

    # 6) Final passes (determinism)
    clean["components"] = sorted(clean["components"], key=lambda x: x["ref"])
    clean["nets"] = sorted(clean["nets"], key=lambda x: x["name"])

    logger.info(
        f"Normalization: done "
        f"({len(clean['components'])} comps, {len(clean['nets'])} nets)"
    )

    return clean


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample = {
        "components": [
            {"ref": " r1 ", "value": "10k", "pins": "1,2"},
            {"ref": "c1", "value": "100nF"},
            {"ref": "U1", "value": "ATmega328P", "pins": ["vcc", "gnd", "pb0"]},
        ],
        "nets": [
            {"net": "vcc", "connections": ["u1:vcc", " r1 : 1 "]},
            {"name": "gnd", "connections": ["u1:gnd", "c1:2", "c1:2"]},
            {"name": "sig", "connections": ["u1:pb0", "r1:2", "c1:1"]},
        ],
        "layout": {
            "r1": {"x": 10.2, "y": 20.7},
            "c1": {"x": 40.9, "y": 60.3},
        },
        "routes": [
            {"net": "sig", "path": [(10.1, 20.2), (40.6, 60.8)]}
        ],
    }

    out = normalize_design(sample)
    from pprint import pprint
    pprint(out)
  
