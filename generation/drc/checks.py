# generation/drc/checks.py

from typing import Dict, Any, List, Tuple
import math

from utils.logger import get_module_logger
from config.settings import settings


logger = get_module_logger(__name__)

# --------------------------------------------------
# CONFIG (from settings)
# --------------------------------------------------
MIN_CLEARANCE = settings.MIN_CLEARANCE
MIN_TRACE_WIDTH = settings.MIN_TRACE_WIDTH
BOARD_WIDTH = settings.BOARD_WIDTH
BOARD_HEIGHT = settings.BOARD_HEIGHT


# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def distance(p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def point_to_segment_distance(px, py, x1, y1, x2, y2):
    """
    Distance from point to line segment
    """
    line_mag = distance((x1, y1), (x2, y2))

    if line_mag < 1e-6:
        return distance((px, py), (x1, y1))

    u = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / (line_mag ** 2)

    if u < 0:
        return distance((px, py), (x1, y1))
    elif u > 1:
        return distance((px, py), (x2, y2))
    else:
        ix = x1 + u * (x2 - x1)
        iy = y1 + u * (y2 - y1)
        return distance((px, py), (ix, iy))


# --------------------------------------------------
# 1. COMPONENT OVERLAP
# --------------------------------------------------
def check_component_overlap(layout: Dict[str, Dict]) -> List[Dict]:
    errors = []
    refs = list(layout.keys())

    for i in range(len(refs)):
        for j in range(i + 1, len(refs)):
            r1, r2 = refs[i], refs[j]
            p1 = layout[r1]
            p2 = layout[r2]

            if p1["x"] == p2["x"] and p1["y"] == p2["y"]:
                errors.append({
                    "type": "OVERLAP",
                    "message": f"{r1} overlaps with {r2}",
                    "refs": [r1, r2]
                })

    return errors


# --------------------------------------------------
# 2. CLEARANCE (COMPONENT ↔ COMPONENT)
# --------------------------------------------------
def check_component_clearance(layout) -> List[Dict]:
    errors = []
    refs = list(layout.keys())

    for i in range(len(refs)):
        for j in range(i + 1, len(refs)):
            r1, r2 = refs[i], refs[j]
            p1 = layout[r1]
            p2 = layout[r2]

            d = distance((p1["x"], p1["y"]), (p2["x"], p2["y"]))

            if d < MIN_CLEARANCE:
                errors.append({
                    "type": "CLEARANCE",
                    "message": f"Clearance violation: {r1} ↔ {r2}",
                    "distance": d,
                    "min_required": MIN_CLEARANCE
                })

    return errors


# --------------------------------------------------
# 3. ROUTE WIDTH CHECK
# --------------------------------------------------
def check_trace_width(routes) -> List[Dict]:
    errors = []

    for r in routes:
        width = r.get("width", MIN_TRACE_WIDTH)

        if width < MIN_TRACE_WIDTH:
            errors.append({
                "type": "TRACE_WIDTH",
                "message": f"Trace too thin in net {r['net']}",
                "width": width,
                "min_required": MIN_TRACE_WIDTH
            })

    return errors


# --------------------------------------------------
# 4. ROUTE ↔ COMPONENT CLEARANCE
# --------------------------------------------------
def check_route_component_clearance(layout, routes):
    errors = []

    for route in routes:
        path = route.get("path", [])

        for ref, pos in layout.items():
            px, py = pos["x"], pos["y"]

            for i in range(len(path) - 1):
                x1, y1 = path[i]
                x2, y2 = path[i + 1]

                d = point_to_segment_distance(px, py, x1, y1, x2, y2)

                if d < MIN_CLEARANCE:
                    errors.append({
                        "type": "ROUTE_COMPONENT_CLEARANCE",
                        "message": f"Route too close to {ref}",
                        "net": route["net"],
                        "distance": d
                    })

    return errors


# --------------------------------------------------
# 5. ROUTE ↔ ROUTE CLEARANCE
# --------------------------------------------------
def check_route_clearance(routes):
    errors = []

    for i in range(len(routes)):
        for j in range(i + 1, len(routes)):
            r1 = routes[i]
            r2 = routes[j]

            path1 = r1.get("path", [])
            path2 = r2.get("path", [])

            for p1 in path1:
                for p2 in path2:
                    d = distance(p1, p2)

                    if d < MIN_CLEARANCE:
                        errors.append({
                            "type": "ROUTE_CLEARANCE",
                            "message": f"Routes too close: {r1['net']} ↔ {r2['net']}",
                            "distance": d
                        })

    return errors


# --------------------------------------------------
# 6. BOUNDARY CHECK
# --------------------------------------------------
def check_board_boundaries(layout):
    errors = []

    for ref, pos in layout.items():
        x, y = pos["x"], pos["y"]

        if not (0 <= x <= BOARD_WIDTH and 0 <= y <= BOARD_HEIGHT):
            errors.append({
                "type": "BOUNDARY",
                "message": f"{ref} outside board boundary",
                "position": (x, y)
            })

    return errors


# --------------------------------------------------
# 7. UNCONNECTED NETS
# --------------------------------------------------
def check_unconnected_nets(nets, routes):
    errors = []

    routed_pairs = set()
    for r in routes:
        routed_pairs.add((r.get("from"), r.get("to")))

    for net in nets:
        conns = net.get("connections", [])

        for i in range(len(conns) - 1):
            r1 = conns[i].split(":")[0]
            r2 = conns[i + 1].split(":")[0]

            if (r1, r2) not in routed_pairs and (r2, r1) not in routed_pairs:
                errors.append({
                    "type": "UNCONNECTED",
                    "message": f"Net {net['name']} not fully routed",
                    "refs": [r1, r2]
                })

    return errors


# --------------------------------------------------
# MAIN DRC RUNNER
# --------------------------------------------------
def run_drc(design: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run all DRC checks and return structured report
    """

    logger.info("Running DRC checks")

    layout = design.get("layout", {})
    routes = design.get("routes", [])
    nets = design.get("nets", [])

    all_errors = []

    # Run checks
    all_errors += check_component_overlap(layout)
    all_errors += check_component_clearance(layout)
    all_errors += check_trace_width(routes)
    all_errors += check_route_component_clearance(layout, routes)
    all_errors += check_route_clearance(routes)
    all_errors += check_board_boundaries(layout)
    all_errors += check_unconnected_nets(nets, routes)

    report = {
        "total_errors": len(all_errors),
        "errors": all_errors,
        "status": "PASS" if len(all_errors) == 0 else "FAIL"
    }

    logger.info(f"DRC completed: {report['total_errors']} issues found")

    return report


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample_design = {
        "layout": {
            "R1": {"x": 10, "y": 10},
            "C1": {"x": 10, "y": 10},  # overlap
        },
        "routes": [
            {
                "net": "VCC",
                "from": "R1",
                "to": "C1",
                "path": [(10, 10), (20, 10)],
                "width": 0.1
            }
        ],
        "nets": [
            {"name": "VCC", "connections": ["R1:1", "C1:1"]}
        ]
    }

    result = run_drc(sample_design)
    print(result)
  
