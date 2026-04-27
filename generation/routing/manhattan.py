# generation/routing/manhattan.py
from typing import Dict, Any, List, Tuple
import math

from utils.logger import get_module_logger
from config.settings import settings

logger = get_module_logger(__name__)

GRID_SIZE = settings.GRID_SIZE

# --------------------------------------------------
# COMPONENT TYPE DETECTION (POWER / HEAT)
# --------------------------------------------------
def is_power_component(comp):
    keywords = ["regulator", "7805", "power", "mosfet", "buck", "boost"]
    return any(k in comp.get("value", "").lower() for k in keywords)

def is_heat_component(comp):
    keywords = ["mosfet", "driver", "cpu", "mcu", "amp"]
    return any(k in comp.get("value", "").lower() for k in keywords)

# --------------------------------------------------
# DISTANCE
# --------------------------------------------------
def manhattan_distance(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

# --------------------------------------------------
# THERMAL / POWER COST FUNCTION
# --------------------------------------------------
def routing_cost(p1, p2, comp_map, ref1, ref2):
    """
    Increase cost for:
    - Power nets → prefer short paths
    - Heat components → avoid clustering
    """

    base = manhattan_distance(p1, p2)

    comp1 = comp_map.get(ref1, {})
    comp2 = comp_map.get(ref2, {})

    # Power components → shorter routing preferred
    if is_power_component(comp1) or is_power_component(comp2):
        base *= 0.5

    # Heat components → spread out (penalty if too close)
    if is_heat_component(comp1) and is_heat_component(comp2):
        if base < 30:
            base *= 2

    return base

# --------------------------------------------------
# SIMPLE MANHATTAN ROUTE
# --------------------------------------------------
def manhattan_route(p1: Tuple[int, int], p2: Tuple[int, int]):
    """
    L-shaped routing
    """
    x1, y1 = p1
    x2, y2 = p2

    return [
        (x1, y1),
        (x2, y1),
        (x2, y2)
    ]


# --------------------------------------------------
# ADVANCED ROUTE (MULTI-OPTION)
# --------------------------------------------------
def best_route(p1, p2, comp_map, ref1, ref2):
    """
    Try both L-shapes and pick lower cost
    """

    # Option 1
    route1 = [(p1[0], p1[1]), (p2[0], p1[1]), (p2[0], p2[1])]
    cost1 = routing_cost(p1, p2, comp_map, ref1, ref2)

    # Option 2
    route2 = [(p1[0], p1[1]), (p1[0], p2[1]), (p2[0], p2[1])]
    cost2 = routing_cost(p1, p2, comp_map, ref1, ref2)

    return route1 if cost1 <= cost2 else route2

# --------------------------------------------------
# BUILD COMPONENT MAP
# --------------------------------------------------
def build_component_map(design):
    return {c["ref"]: c for c in design.get("components", [])}

# --------------------------------------------------
# MAIN ROUTER
# --------------------------------------------------
def auto_route(design: Dict[str, Any]):
    """
    Generate routes for all nets
    """

    logger.info("Starting Manhattan routing")

    layout = design.get("layout", {})
    nets = design.get("nets", [])

    if not layout:
        logger.warning("No layout found. Skipping routing.")
        design["routes"] = []
        return design

    comp_map = build_component_map(design)
    routes = []

    for net in nets:
        connections = net.get("connections", [])

        # Connect sequentially
        for i in range(len(connections) - 1):
            ref1 = connections[i].split(":")[0]
            ref2 = connections[i + 1].split(":")[0]

            if ref1 not in layout or ref2 not in layout:
                continue

            p1 = (layout[ref1]["x"], layout[ref1]["y"])
            p2 = (layout[ref2]["x"], layout[ref2]["y"])

            route_path = best_route(p1, p2, comp_map, ref1, ref2)

            routes.append({
                "net": net["name"],
                "from": ref1,
                "to": ref2,
                "path": route_path
            })

    design["routes"] = routes

    logger.info(f"Routing completed: {len(routes)} routes generated")

    return design

# --------------------------------------------------
# OPTIONAL: POWER NET OPTIMIZATION
# --------------------------------------------------
def optimize_power_routes(design):
    """
    Post-process: ensure power nets are shortest
    """

    for route in design.get("routes", []):
        if "vcc" in route["net"].lower() or "power" in route["net"].lower():
            path = route["path"]

            # Straighten if possible
            if len(path) == 3:
                p1, _, p3 = path
                route["path"] = [p1, p3]

    return design

# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample = {
        "components": [
            {"ref": "U1", "value": "ATmega"},
            {"ref": "U2", "value": "7805"},
            {"ref": "R1", "value": "10k"},
        ],
        "layout": {
            "U1": {"x": 10, "y": 10},
            "U2": {"x": 60, "y": 60},
            "R1": {"x": 30, "y": 20},
        },
        "nets": [
            {"name": "VCC", "connections": ["U2:OUT", "U1:VCC"]},
            {"name": "SIG", "connections": ["U1:PB0", "R1:1"]},
        ]
    }

    routed = auto_route(sample)
    routed = optimize_power_routes(routed)

    for r in routed["routes"]:
        print(r)
      
