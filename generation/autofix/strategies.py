# generation/autofix/strategies.py

from typing import Dict, Any, Callable, List
import random

from utils.logger import get_module_logger
from config.settings import settings

logger = get_module_logger(__name__)

GRID = settings.GRID_SIZE
MIN_CLEARANCE = settings.MIN_CLEARANCE
BOARD_WIDTH = settings.BOARD_WIDTH
BOARD_HEIGHT = settings.BOARD_HEIGHT


# --------------------------------------------------
# BASE STRATEGY CLASS
# --------------------------------------------------
class FixStrategy:
    def __init__(self, name: str, priority: int = 1):
        self.name = name
        self.priority = priority

    def apply(self, design: Dict[str, Any], error: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


# --------------------------------------------------
# STRATEGY: OVERLAP FIX
# --------------------------------------------------
class OverlapFixStrategy(FixStrategy):
    def __init__(self):
        super().__init__("OVERLAP", priority=10)

    def apply(self, design, error):
        refs = error.get("refs", [])
        layout = design.get("layout", {})

        for ref in refs:
            if ref in layout:
                layout[ref]["x"] += random.randint(GRID, GRID * 3)
                layout[ref]["y"] += random.randint(GRID, GRID * 3)

        logger.debug(f"Overlap fixed for {refs}")
        return design


# --------------------------------------------------
# STRATEGY: CLEARANCE FIX
# --------------------------------------------------
class ClearanceFixStrategy(FixStrategy):
    def __init__(self):
        super().__init__("CLEARANCE", priority=9)

    def apply(self, design, error):
        layout = design.get("layout", {})

        for ref, pos in layout.items():
            pos["x"] += random.randint(1, GRID)
            pos["y"] += random.randint(1, GRID)

        logger.debug("Clearance adjusted globally")
        return design


# --------------------------------------------------
# STRATEGY: TRACE WIDTH FIX
# --------------------------------------------------
class TraceWidthFixStrategy(FixStrategy):
    def __init__(self):
        super().__init__("TRACE_WIDTH", priority=8)

    def apply(self, design, error):
        for route in design.get("routes", []):
            route["width"] = max(route.get("width", 0), MIN_CLEARANCE)

        logger.debug("Trace width increased")
        return design


# --------------------------------------------------
# STRATEGY: BOUNDARY FIX
# --------------------------------------------------
class BoundaryFixStrategy(FixStrategy):
    def __init__(self):
        super().__init__("BOUNDARY", priority=9)

    def apply(self, design, error):
        layout = design.get("layout", {})

        for ref, pos in layout.items():
            pos["x"] = max(0, min(pos["x"], BOARD_WIDTH))
            pos["y"] = max(0, min(pos["y"], BOARD_HEIGHT))

        logger.debug("Boundary enforced")
        return design


# --------------------------------------------------
# STRATEGY: ROUTE CLEARANCE FIX
# --------------------------------------------------
class RouteFixStrategy(FixStrategy):
    def __init__(self):
        super().__init__("ROUTE_CLEARANCE", priority=7)

    def apply(self, design, error):
        from generation.routing.autorouter import autoroute
        logger.debug("Re-routing due to route clearance")
        return autoroute(design)


# --------------------------------------------------
# STRATEGY: UNCONNECTED FIX
# --------------------------------------------------
class UnconnectedFixStrategy(FixStrategy):
    def __init__(self):
        super().__init__("UNCONNECTED", priority=10)

    def apply(self, design, error):
        from generation.routing.autorouter import autoroute
        logger.debug("Routing missing connections")
        return autoroute(design)


# --------------------------------------------------
# STRATEGY: THERMAL SPREAD
# --------------------------------------------------
class ThermalFixStrategy(FixStrategy):
    def __init__(self):
        super().__init__("THERMAL", priority=6)

    def apply(self, design, error):
        layout = design.get("layout", {})
        comps = design.get("components", [])

        heat_keywords = ["mosfet", "cpu", "mcu", "driver"]

        heat_refs = [
            c["ref"] for c in comps
            if any(k in c.get("value", "").lower() for k in heat_keywords)
        ]

        for ref in heat_refs:
            if ref in layout:
                layout[ref]["x"] += GRID * 2
                layout[ref]["y"] += GRID * 2

        logger.debug("Thermal spacing applied")
        return design


# --------------------------------------------------
# STRATEGY: POWER OPTIMIZATION
# --------------------------------------------------
class PowerFixStrategy(FixStrategy):
    def __init__(self):
        super().__init__("POWER", priority=6)

    def apply(self, design, error):
        layout = design.get("layout", {})
        comps = design.get("components", [])

        for comp in comps:
            val = comp.get("value", "").lower()
            if "7805" in val or "regulator" in val:
                ref = comp["ref"]
                if ref in layout:
                    layout[ref]["x"] = GRID
                    layout[ref]["y"] = GRID

        logger.debug("Power components repositioned")
        return design


# --------------------------------------------------
# STRATEGY REGISTRY
# --------------------------------------------------
STRATEGY_REGISTRY: Dict[str, FixStrategy] = {
    "OVERLAP": OverlapFixStrategy(),
    "CLEARANCE": ClearanceFixStrategy(),
    "TRACE_WIDTH": TraceWidthFixStrategy(),
    "BOUNDARY": BoundaryFixStrategy(),
    "ROUTE_CLEARANCE": RouteFixStrategy(),
    "ROUTE_COMPONENT_CLEARANCE": RouteFixStrategy(),
    "UNCONNECTED": UnconnectedFixStrategy(),
}


# Optional global strategies
GLOBAL_STRATEGIES: List[FixStrategy] = [
    ThermalFixStrategy(),
    PowerFixStrategy(),
]


# --------------------------------------------------
# APPLY STRATEGIES
# --------------------------------------------------
def apply_strategies(design: Dict[str, Any], errors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Apply fixes based on error types + global improvements
    """

    # Sort errors by priority
    sorted_errors = sorted(
        errors,
        key=lambda e: STRATEGY_REGISTRY.get(e.get("type"), FixStrategy("", 0)).priority,
        reverse=True
    )

    for err in sorted_errors:
        etype = err.get("type")
        strategy = STRATEGY_REGISTRY.get(etype)

        if strategy:
            design = strategy.apply(design, err)

    # Apply global improvements
    for strategy in GLOBAL_STRATEGIES:
        design = strategy.apply(design, {})

    return design


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample_design = {
        "components": [
            {"ref": "U1", "value": "ATmega"},
            {"ref": "U2", "value": "7805"},
        ],
        "layout": {
            "U1": {"x": 10, "y": 10},
            "U2": {"x": 10, "y": 10},
        },
        "routes": [],
        "nets": []
    }

    errors = [
        {"type": "OVERLAP", "refs": ["U1", "U2"]},
        {"type": "TRACE_WIDTH"}
    ]

    result = apply_strategies(sample_design, errors)

    print(result["layout"])
  
