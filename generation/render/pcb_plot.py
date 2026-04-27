# generation/render/pcb_plot.py

import matplotlib.pyplot as plt
from typing import Dict, Any

from utils.output_manager import OutputManager
from utils.logger import get_module_logger
from config.settings import settings


logger = get_module_logger(__name__)
output_manager = OutputManager()


# --------------------------------------------------
# DEFAULT STYLE CONFIG
# --------------------------------------------------
COMPONENT_COLOR = "blue"
ROUTE_COLOR = "green"
TEXT_COLOR = "black"
NET_COLORS = ["red", "green", "blue", "orange", "purple"]

FIG_SIZE = (8, 6)


# --------------------------------------------------
# SAFE GETTERS
# --------------------------------------------------
def get_layout(design: Dict[str, Any]):
    return design.get("layout", {})


def get_routes(design: Dict[str, Any]):
    return design.get("routes", [])


def get_components(design: Dict[str, Any]):
    return design.get("components", [])


# --------------------------------------------------
# DRAW COMPONENTS
# --------------------------------------------------
def draw_components(ax, layout):
    for ref, pos in layout.items():
        x = pos.get("x", 0)
        y = pos.get("y", 0)

        ax.scatter(x, y)
        ax.text(x, y, ref, fontsize=8)

    logger.debug(f"Rendered {len(layout)} components")


# --------------------------------------------------
# DRAW ROUTES
# --------------------------------------------------
def draw_routes(ax, routes):
    for idx, route in enumerate(routes):
        path = route.get("path", [])
        if not path or len(path) < 2:
            continue

        xs = [p[0] for p in path]
        ys = [p[1] for p in path]

        color = NET_COLORS[idx % len(NET_COLORS)]

        ax.plot(xs, ys, color=color, linewidth=1)

    logger.debug(f"Rendered {len(routes)} routes")


# --------------------------------------------------
# DRAW BOARD GRID
# --------------------------------------------------
def draw_grid(ax):
    ax.grid(True, linestyle="--", linewidth=0.5)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")


# --------------------------------------------------
# SET BOUNDS
# --------------------------------------------------
def set_bounds(ax, layout):
    if not layout:
        return

    xs = [pos["x"] for pos in layout.values()]
    ys = [pos["y"] for pos in layout.values()]

    padding = 10

    ax.set_xlim(min(xs) - padding, max(xs) + padding)
    ax.set_ylim(min(ys) - padding, max(ys) + padding)


# --------------------------------------------------
# MAIN FUNCTION
# --------------------------------------------------
def draw_pcb(design: Dict[str, Any], save: bool = True):
    """
    Render PCB layout and save image.

    Args:
        design: dict with layout + routes
        save: whether to save output image

    Returns:
        Path to saved image OR None
    """

    try:
        layout = get_layout(design)
        routes = get_routes(design)

        if not layout:
            logger.warning("No layout found in design")
        
        fig, ax = plt.subplots(figsize=FIG_SIZE)

        # Draw elements
        draw_components(ax, layout)
        draw_routes(ax, routes)
        draw_grid(ax)
        set_bounds(ax, layout)

        ax.set_title("PCB Layout Visualization")

        # Save image
        if save:
            path = output_manager.save_image(fig, "pcb_layout")
            logger.info(f"PCB image saved at {path}")
        else:
            path = None

        plt.close(fig)

        return path

    except Exception as e:
        logger.error(f"PCB rendering failed: {e}")
        return None


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample_design = {
        "layout": {
            "R1": {"x": 10, "y": 20},
            "C1": {"x": 40, "y": 20},
            "U1": {"x": 25, "y": 50},
        },
        "routes": [
            {"net": "VCC", "path": [(10, 20), (25, 20), (25, 50)]},
            {"net": "GND", "path": [(40, 20), (25, 20), (25, 50)]},
        ]
    }

    draw_pcb(sample_design)
  
