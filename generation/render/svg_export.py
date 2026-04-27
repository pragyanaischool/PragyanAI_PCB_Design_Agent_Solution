# generation/render/svg_export.py

from typing import Dict, Any, Tuple
from xml.etree.ElementTree import Element, SubElement, ElementTree

from utils.output_manager import OutputManager
from utils.logger import get_module_logger

logger = get_module_logger(__name__)
output_manager = OutputManager()


# --------------------------------------------------
# SVG ROOT
# --------------------------------------------------
def create_svg_root(width=800, height=600):
    return Element(
        "svg",
        width=str(width),
        height=str(height),
        viewBox=f"0 0 {width} {height}",
        xmlns="http://www.w3.org/2000/svg"
    )


# --------------------------------------------------
# SCALING FUNCTION
# --------------------------------------------------
def scale_point(x, y, max_x, max_y, width=800, height=600):
    if max_x == 0 or max_y == 0:
        return x, y

    sx = (x / max_x) * (width - 40) + 20
    sy = (y / max_y) * (height - 40) + 20

    return sx, sy


# --------------------------------------------------
# EXPORT PCB SVG
# --------------------------------------------------
def export_pcb_svg(design: Dict[str, Any]):
    logger.info("Exporting PCB to SVG")

    svg = create_svg_root()

    layout = design.get("layout", {})
    routes = design.get("routes", [])

    if not layout:
        logger.warning("No layout found")
        return None

    # Get bounds
    max_x = max(pos["x"] for pos in layout.values())
    max_y = max(pos["y"] for pos in layout.values())

    # Draw routes
    for route in routes:
        path = route.get("path", [])

        for i in range(len(path) - 1):
            x1, y1 = scale_point(*path[i], max_x, max_y)
            x2, y2 = scale_point(*path[i + 1], max_x, max_y)

            SubElement(
                svg,
                "line",
                x1=str(x1),
                y1=str(y1),
                x2=str(x2),
                y2=str(y2),
                stroke="green",
                stroke_width="2"
            )

    # Draw components
    for ref, pos in layout.items():
        x, y = scale_point(pos["x"], pos["y"], max_x, max_y)

        # Component node
        SubElement(svg, "circle", cx=str(x), cy=str(y), r="6", fill="blue")

        # Label
        SubElement(
            svg,
            "text",
            x=str(x + 5),
            y=str(y - 5),
            fill="black",
            font_size="10"
        ).text = ref

    # Save file
    filename = output_manager.generate_filename("pcb", "svg")
    path = output_manager.dirs["images"] / filename

    ElementTree(svg).write(path)

    logger.info(f"PCB SVG saved: {path}")

    return path


# --------------------------------------------------
# EXPORT SCHEMATIC SVG
# --------------------------------------------------
def export_schematic_svg(design: Dict[str, Any]):
    logger.info("Exporting schematic to SVG")

    svg = create_svg_root()

    components = design.get("components", [])
    nets = design.get("nets", [])

    y_offset = 30

    # Draw components list
    SubElement(svg, "text", x="10", y="20", fill="black").text = "Components"

    for comp in components:
        text = f"{comp.get('ref')} ({comp.get('value', '')})"

        SubElement(
            svg,
            "text",
            x="10",
            y=str(y_offset),
            fill="blue",
            font_size="12"
        ).text = text

        y_offset += 20

    # Draw nets
    y_offset += 20
    SubElement(svg, "text", x="10", y=str(y_offset), fill="black").text = "Nets"

    y_offset += 20

    for net in nets:
        text = f"{net.get('name')}: {', '.join(net.get('connections', []))}"

        SubElement(
            svg,
            "text",
            x="10",
            y=str(y_offset),
            fill="green",
            font_size="11"
        ).text = text

        y_offset += 20

    # Save file
    filename = output_manager.generate_filename("schematic", "svg")
    path = output_manager.dirs["images"] / filename

    ElementTree(svg).write(path)

    logger.info(f"Schematic SVG saved: {path}")

    return path


# --------------------------------------------------
# EXPORT COMBINED VIEW
# --------------------------------------------------
def export_full_svg(design: Dict[str, Any]):
    """
    Export both PCB + schematic
    """
    return {
        "pcb": str(export_pcb_svg(design)),
        "schematic": str(export_schematic_svg(design))
    }


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample = {
        "components": [
            {"ref": "R1", "value": "10k"},
            {"ref": "C1", "value": "100nF"},
        ],
        "layout": {
            "R1": {"x": 10, "y": 20},
            "C1": {"x": 40, "y": 60},
        },
        "routes": [
            {"net": "SIG", "path": [(10, 20), (40, 60)]}
        ],
        "nets": [
            {"name": "SIG", "connections": ["R1:1", "C1:1"]}
        ]
    }

    export_full_svg(sample)
  
