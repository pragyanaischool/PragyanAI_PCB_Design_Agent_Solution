#config/constants.py
# config/constants.py

# =========================
# FILE TYPES
# =========================
SUPPORTED_INPUT_TYPES = ["csv", "json", "kicad", "altium"]

# =========================
# DEFAULT FOOTPRINTS
# =========================
DEFAULT_FOOTPRINTS = {
    "resistor": "Resistor_SMD:R_0805",
    "capacitor": "Capacitor_SMD:C_0603",
    "led": "LED_SMD:LED_0805"
}

# =========================
# PCB GRID SETTINGS
# =========================
GRID_SIZE = 10
MAX_BOARD_WIDTH = 200
MAX_BOARD_HEIGHT = 200

# =========================
# ROUTING
# =========================
ROUTING_STYLE = "manhattan"
MAX_ROUTE_ATTEMPTS = 100

# =========================
# DRC RULES
# =========================
DRC_RULES = {
    "min_trace_width": 0.25,
    "min_clearance": 0.2,
    "no_overlap": True
}

# =========================
# AGENT NAMES
# =========================
AGENTS = {
    "parser": "ParsingAgent",
    "normalize": "NormalizationAgent",
    "enrich": "EnrichmentAgent",
    "layout": "LayoutAgent",
    "routing": "RoutingAgent",
    "drc": "DRCAgent",
    "fix": "AutoFixAgent",
    "rag": "RAGAgent",
    "render": "RenderAgent"
}

# =========================
# ERROR TYPES
# =========================
ERROR_TYPES = {
    "OVERLAP": "Component Overlap",
    "CLEARANCE": "Clearance Violation",
    "ROUTE": "Routing Error"
}
