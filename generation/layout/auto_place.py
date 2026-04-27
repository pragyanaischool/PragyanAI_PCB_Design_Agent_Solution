# generation/layout/auto_place.py

import random
from typing import Dict, Any

from config.settings import settings
from utils.logger import get_module_logger
from utils.graph_utils import netlist_to_graph

logger = get_module_logger(__name__)

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
GRID_SIZE = settings.GRID_SIZE
BOARD_WIDTH = settings.BOARD_WIDTH
BOARD_HEIGHT = settings.BOARD_HEIGHT

# --------------------------------------------------
# HELPER: CHECK COLLISION
# --------------------------------------------------
def is_occupied(layout, x, y):
    for pos in layout.values():
        if pos["x"] == x and pos["y"] == y:
            return True
    return False

# --------------------------------------------------
# HELPER: FIND NEXT FREE GRID POSITION
# --------------------------------------------------
def find_free_position(layout):
    for x in range(0, BOARD_WIDTH, GRID_SIZE):
        for y in range(0, BOARD_HEIGHT, GRID_SIZE):
            if not is_occupied(layout, x, y):
                return x, y
    return None

# --------------------------------------------------
# BASIC GRID PLACEMENT
# --------------------------------------------------
def grid_placement(components):
    layout = {}

    x, y = 0, 0

    for comp in components:
        layout[comp["ref"]] = {"x": x, "y": y}

        x += GRID_SIZE
        if x >= BOARD_WIDTH:
            x = 0
            y += GRID_SIZE

    return layout

# --------------------------------------------------
# GRAPH-BASED CLUSTERING
# --------------------------------------------------
def cluster_placement(design):
    """
    Place connected components closer together
    """
    G = netlist_to_graph(design)

    layout = {}
    visited = set()

    clusters = list(G.subgraph(c).nodes() for c in nx.connected_components(G)) if G else []

    x_offset = 0

    for cluster in clusters:
        y_offset = 0

        for node in cluster:
            try:
                ref = node.split(":")[0]

                if ref in layout:
                    continue

                layout[ref] = {
                    "x": x_offset,
                    "y": y_offset
                }

                y_offset += GRID_SIZE

            except Exception:
                continue

        x_offset += GRID_SIZE * 3

    return layout

# --------------------------------------------------
# IMPROVED PLACEMENT (HYBRID)
# --------------------------------------------------
def smart_placement(design):
    """
    Combines clustering + grid fallback
    """
    components = design.get("components", [])

    if not components:
        return {}

    try:
        layout = {}

        # Try clustering first
        graph_layout = cluster_placement(design)

        for comp in components:
            ref = comp["ref"]

            if ref in graph_layout:
                layout[ref] = graph_layout[ref]
            else:
                pos = find_free_position(layout)
                if pos:
                    layout[ref] = {"x": pos[0], "y": pos[1]}
                else:
                    layout[ref] = {"x": random.randint(0, BOARD_WIDTH),
                                   "y": random.randint(0, BOARD_HEIGHT)}

        return layout

    except Exception as e:
        logger.warning(f"Smart placement failed, fallback to grid: {e}")
        return grid_placement(components)

# --------------------------------------------------
# BOUNDARY CHECK
# --------------------------------------------------
def enforce_boundaries(layout):
    for ref, pos in layout.items():
        pos["x"] = max(0, min(pos["x"], BOARD_WIDTH))
        pos["y"] = max(0, min(pos["y"], BOARD_HEIGHT))
    return layout

# --------------------------------------------------
# MAIN API
# --------------------------------------------------
def auto_place(design: Dict[str, Any], strategy: str = "smart"):
    """
    Auto placement entry point

    Args:
        design: PCB design dict
        strategy: "grid" | "smart"

    Returns:
        Updated design with layout
    """

    logger.info(f"Auto placement started using strategy: {strategy}")

    components = design.get("components", [])
    if not components:
        logger.warning("No components found for placement")
        design["layout"] = {}
        return design

    if strategy == "grid":
        layout = grid_placement(components)
    else:
        layout = smart_placement(design)

    layout = enforce_boundaries(layout)

    design["layout"] = layout

    logger.info(f"Placement completed: {len(layout)} components placed")

    return design

# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample_design = {
        "components": [
            {"ref": "R1"},
            {"ref": "C1"},
            {"ref": "U1"},
            {"ref": "U2"},
        ],
        "nets": [
            {"name": "VCC", "connections": ["U1:1", "R1:1"]},
            {"name": "GND", "connections": ["U1:2", "C1:2"]},
        ]
    }

    result = auto_place(sample_design)

    for k, v in result["layout"].items():
        print(k, v)
      
