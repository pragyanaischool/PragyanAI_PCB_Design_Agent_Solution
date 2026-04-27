# generation/layout/constraints.py

from typing import Dict, Any, List, Tuple
import math

from config.settings import settings
from utils.logger import get_module_logger


logger = get_module_logger(__name__)

BOARD_WIDTH = settings.BOARD_WIDTH
BOARD_HEIGHT = settings.BOARD_HEIGHT
MIN_CLEARANCE = settings.MIN_CLEARANCE
GRID_SIZE = settings.GRID_SIZE


# --------------------------------------------------
# COMPONENT TYPE HELPERS
# --------------------------------------------------
def is_power_component(comp):
    keywords = ["regulator", "7805", "power", "buck", "boost"]
    return any(k in comp.get("value", "").lower() for k in keywords)


def is_heat_component(comp):
    keywords = ["mosfet", "cpu", "mcu", "driver", "amp"]
    return any(k in comp.get("value", "").lower() for k in keywords)


# --------------------------------------------------
# DISTANCE
# --------------------------------------------------
def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


# --------------------------------------------------
# KEEP-OUT ZONES
# --------------------------------------------------
def enforce_keepout(layout, keepouts: List[Tuple[int, int, int, int]]):
    """
    keepouts: list of (x1, y1, x2, y2)
    """
    for ref, pos in layout.items():
        x, y = pos["x"], pos["y"]

        for (x1, y1, x2, y2) in keepouts:
            if x1 <= x <= x2 and y1 <= y <= y2:
                logger.debug(f"{ref} inside keepout → shifting")
                pos["x"] = x2 + GRID_SIZE
                pos["y"] = y2 + GRID_SIZE

    return layout


# --------------------------------------------------
# BOUNDARY ENFORCEMENT
# --------------------------------------------------
def enforce_board_boundaries(layout):
    for ref, pos in layout.items():
        pos["x"] = max(0, min(pos["x"], BOARD_WIDTH))
        pos["y"] = max(0, min(pos["y"], BOARD_HEIGHT))
    return layout


# --------------------------------------------------
# MIN CLEARANCE BETWEEN COMPONENTS
# --------------------------------------------------
def enforce_component_spacing(layout):
    refs = list(layout.keys())

    for i in range(len(refs)):
        for j in range(i + 1, len(refs)):
            r1, r2 = refs[i], refs[j]

            p1 = layout[r1]
            p2 = layout[r2]

            d = distance((p1["x"], p1["y"]), (p2["x"], p2["y"]))

            if d < MIN_CLEARANCE:
                shift = GRID_SIZE
                layout[r2]["x"] += shift
                layout[r2]["y"] += shift

    return layout


# --------------------------------------------------
# POWER ZONE CONSTRAINT
# --------------------------------------------------
def enforce_power_zone(layout, components):
    """
    Place power components near origin (or specific zone)
    """
    for comp in components:
        if is_power_component(comp):
            ref = comp["ref"]
            if ref in layout:
                layout[ref]["x"] = GRID_SIZE
                layout[ref]["y"] = GRID_SIZE

    return layout


# --------------------------------------------------
# THERMAL SPACING CONSTRAINT
# --------------------------------------------------
def enforce_thermal_spacing(layout, components):
    """
    Ensure heat-generating components are spaced apart
    """
    heat_refs = [
        comp["ref"]
        for comp in components
        if is_heat_component(comp)
    ]

    for i in range(len(heat_refs)):
        for j in range(i + 1, len(heat_refs)):
            r1, r2 = heat_refs[i], heat_refs[j]

            if r1 in layout and r2 in layout:
                p1 = layout[r1]
                p2 = layout[r2]

                d = distance((p1["x"], p1["y"]), (p2["x"], p2["y"]))

                if d < 3 * MIN_CLEARANCE:
                    layout[r2]["x"] += GRID_SIZE * 2
                    layout[r2]["y"] += GRID_SIZE * 2

    return layout


# --------------------------------------------------
# GROUPING CONSTRAINT (KEEP CONNECTED COMPONENTS CLOSE)
# --------------------------------------------------
def enforce_grouping(layout, nets):
    """
    Pull connected components closer
    """
    for net in nets:
        refs = [conn.split(":")[0] for conn in net.get("connections", [])]

        for i in range(len(refs) - 1):
            r1 = refs[i]
            r2 = refs[i + 1]

            if r1 in layout and r2 in layout:
                p1 = layout[r1]
                p2 = layout[r2]

                mid_x = (p1["x"] + p2["x"]) // 2
                mid_y = (p1["y"] + p2["y"]) // 2

                layout[r2]["x"] = mid_x
                layout[r2]["y"] = mid_y

    return layout


# --------------------------------------------------
# ALIGNMENT CONSTRAINT (OPTIONAL)
# --------------------------------------------------
def enforce_alignment(layout, axis="x"):
    """
    Align components along x or y axis
    """
    if axis == "x":
        avg = sum(pos["x"] for pos in layout.values()) // len(layout)
        for pos in layout.values():
            pos["x"] = avg
    elif axis == "y":
        avg = sum(pos["y"] for pos in layout.values()) // len(layout)
        for pos in layout.values():
            pos["y"] = avg

    return layout


# --------------------------------------------------
# MAIN CONSTRAINT ENGINE
# --------------------------------------------------
def apply_constraints(design: Dict[str, Any], constraints: Dict[str, Any] = None):
    """
    Apply all constraints sequentially
    """

    logger.info("Applying placement constraints")

    layout = design.get("layout", {})
    components = design.get("components", [])
    nets = design.get("nets", [])

    if not layout:
        logger.warning("No layout found for constraint application")
        return design

    constraints = constraints or {}

    # 1. Keepouts
    keepouts = constraints.get("keepouts", [])
    layout = enforce_keepout(layout, keepouts)

    # 2. Board boundaries
    layout = enforce_board_boundaries(layout)

    # 3. Component spacing
    layout = enforce_component_spacing(layout)

    # 4. Power zone
    if constraints.get("power_zone", True):
        layout = enforce_power_zone(layout, components)

    # 5. Thermal spacing
    if constraints.get("thermal", True):
        layout = enforce_thermal_spacing(layout, components)

    # 6. Grouping (connectivity)
    if constraints.get("grouping", True):
        layout = enforce_grouping(layout, nets)

    # 7. Alignment (optional)
    if constraints.get("align"):
        layout = enforce_alignment(layout, constraints["align"])

    design["layout"] = layout

    logger.info("Constraints applied successfully")

    return design


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample = {
        "components": [
            {"ref": "U1", "value": "ATmega"},
            {"ref": "U2", "value": "7805"},
            {"ref": "Q1", "value": "MOSFET"},
        ],
        "layout": {
            "U1": {"x": 10, "y": 10},
            "U2": {"x": 12, "y": 10},
            "Q1": {"x": 15, "y": 10},
        },
        "nets": [
            {"name": "VCC", "connections": ["U2:OUT", "U1:VCC"]},
        ]
    }

    constraints = {
        "keepouts": [(5, 5, 15, 15)],
        "power_zone": True,
        "thermal": True,
        "grouping": True
    }

    result = apply_constraints(sample, constraints)

    for k, v in result["layout"].items():
        print(k, v)
