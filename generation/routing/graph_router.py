# generation/routing/graph_router.py

from typing import Dict, Any, Tuple, List
import heapq

from config.settings import settings
from utils.logger import get_module_logger


logger = get_module_logger(__name__)

GRID = settings.GRID_SIZE
WIDTH = settings.BOARD_WIDTH
HEIGHT = settings.BOARD_HEIGHT


# --------------------------------------------------
# GRID HELPERS
# --------------------------------------------------
def neighbors(node: Tuple[int, int]):
    x, y = node
    return [
        (x + GRID, y),
        (x - GRID, y),
        (x, y + GRID),
        (x, y - GRID),
    ]


def in_bounds(node):
    x, y = node
    return 0 <= x <= WIDTH and 0 <= y <= HEIGHT


# --------------------------------------------------
# OBSTACLE MAP
# --------------------------------------------------
def build_obstacles(design):
    obstacles = set()

    # Components as obstacles
    for pos in design.get("layout", {}).values():
        obstacles.add((pos["x"], pos["y"]))

    # Existing routes
    for route in design.get("routes", []):
        for p in route.get("path", []):
            obstacles.add(p)

    return obstacles


# --------------------------------------------------
# HEURISTIC (A*)
# --------------------------------------------------
def heuristic(a: Tuple[int, int], b: Tuple[int, int]):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


# --------------------------------------------------
# COST FUNCTION (POWER + THERMAL AWARE)
# --------------------------------------------------
def routing_cost(node, comp_map, ref1, ref2):
    base = 1

    comp1 = comp_map.get(ref1, {})
    comp2 = comp_map.get(ref2, {})

    val1 = comp1.get("value", "").lower()
    val2 = comp2.get("value", "").lower()

    # Power nets → prefer direct routes
    if "power" in val1 or "7805" in val1:
        base *= 0.5

    # Heat sources → avoid congestion
    if "mosfet" in val1 or "mosfet" in val2:
        base *= 2

    return base


# --------------------------------------------------
# A* ROUTER
# --------------------------------------------------
def a_star(start, goal, obstacles, comp_map, ref1, ref2):
    open_set = []
    heapq.heappush(open_set, (0, start))

    came_from = {}
    g_score = {start: 0}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            return reconstruct_path(came_from, current)

        for nxt in neighbors(current):
            if not in_bounds(nxt):
                continue

            if nxt in obstacles and nxt != goal:
                continue

            tentative_g = g_score[current] + routing_cost(
                nxt, comp_map, ref1, ref2
            )

            if nxt not in g_score or tentative_g < g_score[nxt]:
                came_from[nxt] = current
                g_score[nxt] = tentative_g
                f_score = tentative_g + heuristic(nxt, goal)
                heapq.heappush(open_set, (f_score, nxt))

    return None


# --------------------------------------------------
# PATH RECONSTRUCTION
# --------------------------------------------------
def reconstruct_path(came_from, current):
    path = [current]

    while current in came_from:
        current = came_from[current]
        path.append(current)

    path.reverse()
    return path


# --------------------------------------------------
# COMPONENT MAP
# --------------------------------------------------
def build_component_map(design):
    return {c["ref"]: c for c in design.get("components", [])}


# --------------------------------------------------
# MAIN GRAPH ROUTER
# --------------------------------------------------
def graph_route(design: Dict[str, Any]):
    logger.info("Starting graph-based routing")

    layout = design.get("layout", {})
    nets = design.get("nets", [])

    if not layout:
        logger.warning("No layout found")
        return design

    obstacles = build_obstacles(design)
    comp_map = build_component_map(design)

    routes = []

    for net in nets:
        conns = net.get("connections", [])

        for i in range(len(conns) - 1):
            ref1 = conns[i].split(":")[0]
            ref2 = conns[i + 1].split(":")[0]

            if ref1 not in layout or ref2 not in layout:
                continue

            start = (layout[ref1]["x"], layout[ref1]["y"])
            goal = (layout[ref2]["x"], layout[ref2]["y"])

            path = a_star(start, goal, obstacles, comp_map, ref1, ref2)

            if path:
                routes.append({
                    "net": net["name"],
                    "from": ref1,
                    "to": ref2,
                    "path": path
                })

                # Add to obstacles (avoid overlap for next routes)
                for p in path:
                    obstacles.add(p)

            else:
                logger.warning(f"Failed route: {ref1} → {ref2}")

    design["routes"] = routes

    logger.info(f"Graph routing completed: {len(routes)} routes")

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

    routed = graph_route(sample)

    for r in routed["routes"]:
        print(r)
