# generation/routing/autorouter.py

from typing import Dict, Any, List, Tuple, Set
import copy
import math

from utils.logger import get_module_logger
from config.settings import settings

from generation.routing.manhattan import auto_route as manhattan_route
from generation.routing.graph_router import graph_route


logger = get_module_logger(__name__)

GRID = settings.GRID_SIZE
MAX_PASSES = settings.MAX_ROUTE_ATTEMPTS


# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def _pairwise_connections(net):
    conns = net.get("connections", [])
    pairs = []
    for i in range(len(conns) - 1):
        r1 = conns[i].split(":")[0]
        r2 = conns[i + 1].split(":")[0]
        pairs.append((r1, r2))
    return pairs


def _collect_routed_pairs(routes: List[Dict[str, Any]]) -> Set[Tuple[str, str]]:
    pairs = set()
    for r in routes:
        a = r.get("from")
        b = r.get("to")
        if a and b:
            pairs.add((a, b))
            pairs.add((b, a))
    return pairs


def _distance(p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


# --------------------------------------------------
# CONGESTION MAP (simple heatmap on grid points)
# --------------------------------------------------
def build_congestion_map(design: Dict[str, Any]) -> Dict[Tuple[int, int], int]:
    congestion = {}

    # Routes increase congestion
    for route in design.get("routes", []):
        for p in route.get("path", []):
            congestion[p] = congestion.get(p, 0) + 2

    # Components are strong obstacles
    for pos in design.get("layout", {}).values():
        p = (pos["x"], pos["y"])
        congestion[p] = congestion.get(p, 0) + 5

    return congestion


def congestion_penalty(node: Tuple[int, int], congestion: Dict[Tuple[int, int], int]) -> float:
    return 1.0 + congestion.get(node, 0) * 0.2


# --------------------------------------------------
# FILTER UNROUTED PAIRS
# --------------------------------------------------
def get_unrouted_pairs(design: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    """
    Returns list of (net_name, ref1, ref2) that are not routed
    """
    nets = design.get("nets", [])
    routes = design.get("routes", [])
    routed = _collect_routed_pairs(routes)

    missing = []

    for net in nets:
        for (r1, r2) in _pairwise_connections(net):
            if (r1, r2) not in routed:
                missing.append((net.get("name", "NET"), r1, r2))

    return missing


# --------------------------------------------------
# PASS 1: FAST (MANHATTAN)
# --------------------------------------------------
def fast_pass(design: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("Autorouter: Fast pass (Manhattan)")
    return manhattan_route(design)


# --------------------------------------------------
# PASS 2: ADVANCED (GRAPH / A*)
# --------------------------------------------------
def advanced_pass(design: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("Autorouter: Advanced pass (Graph A*)")
    return graph_route(design)


# --------------------------------------------------
# PASS 3: RETRY FAILED WITH RELAXATION
# --------------------------------------------------
def retry_pass(design: Dict[str, Any], attempts: int = 2) -> Dict[str, Any]:
    """
    Re-route only missing connections using advanced router.
    """
    logger.info("Autorouter: Retry pass")

    for attempt in range(attempts):
        missing = get_unrouted_pairs(design)
        if not missing:
            break

        logger.info(f"Retry attempt {attempt+1}, missing: {len(missing)}")

        # Re-run advanced router (it uses existing routes as obstacles)
        design = graph_route(design)

    return design


# --------------------------------------------------
# OPTIONAL: POWER ROUTE OPTIMIZATION
# --------------------------------------------------
def optimize_power_routes(design: Dict[str, Any]) -> Dict[str, Any]:
    """
    Straighten short power nets where possible
    """
    for route in design.get("routes", []):
        net = route.get("net", "").lower()
        if "vcc" in net or "power" in net:
            path = route.get("path", [])
            if len(path) >= 2:
                route["path"] = [path[0], path[-1]]
    return design


# --------------------------------------------------
# OPTIONAL: SMOOTH ROUTES (remove redundant points)
# --------------------------------------------------
def smooth_routes(design: Dict[str, Any]) -> Dict[str, Any]:
    def is_collinear(a, b, c):
        return (b[0]-a[0])*(c[1]-b[1]) == (b[1]-a[1])*(c[0]-b[0])

    for route in design.get("routes", []):
        path = route.get("path", [])
        if len(path) <= 2:
            continue

        new_path = [path[0]]
        for i in range(1, len(path)-1):
            if not is_collinear(path[i-1], path[i], path[i+1]):
                new_path.append(path[i])
        new_path.append(path[-1])

        route["path"] = new_path

    return design


# --------------------------------------------------
# MAIN AUTOROUTER
# --------------------------------------------------
def autoroute(
    design: Dict[str, Any],
    strategy: str = "hybrid",
    optimize: bool = True
) -> Dict[str, Any]:
    """
    strategy:
        - "fast"     → Manhattan only
        - "advanced" → Graph A*
        - "hybrid"   → Fast + Advanced + Retry (recommended)
    """

    logger.info(f"Autorouter started with strategy: {strategy}")

    if not design.get("layout"):
        logger.warning("No layout found. Cannot route.")
        design["routes"] = []
        return design

    # Work on a copy to avoid side effects
    current = copy.deepcopy(design)
    current["routes"] = current.get("routes", [])

    # --------------------------------------------------
    # STRATEGY EXECUTION
    # --------------------------------------------------
    if strategy == "fast":
        current = fast_pass(current)

    elif strategy == "advanced":
        current = advanced_pass(current)

    else:  # hybrid
        current = fast_pass(current)
        current = advanced_pass(current)
        current = retry_pass(current, attempts=3)

    # --------------------------------------------------
    # OPTIONAL OPTIMIZATION
    # --------------------------------------------------
    if optimize:
        current = optimize_power_routes(current)
        current = smooth_routes(current)

    # Final check
    missing = get_unrouted_pairs(current)
    if missing:
        logger.warning(f"Autorouter finished with {len(missing)} unrouted connections")
    else:
        logger.info("Autorouter completed successfully (all connections routed)")

    return current


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample = {
        "components": [
            {"ref": "U1", "value": "ATmega"},
            {"ref": "U2", "value": "7805"},
            {"ref": "R1", "value": "10k"},
            {"ref": "C1", "value": "100nF"},
        ],
        "layout": {
            "U1": {"x": 10, "y": 10},
            "U2": {"x": 80, "y": 80},
            "R1": {"x": 30, "y": 20},
            "C1": {"x": 50, "y": 40},
        },
        "nets": [
            {"name": "VCC", "connections": ["U2:OUT", "U1:VCC"]},
            {"name": "SIG", "connections": ["U1:PB0", "R1:1", "C1:1"]},
        ],
        "routes": []
    }

    routed = autoroute(sample, strategy="hybrid")

    for r in routed["routes"]:
        print(r)
      
