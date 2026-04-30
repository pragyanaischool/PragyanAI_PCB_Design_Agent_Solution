# orchestration/llm/tools.py

from typing import Dict, Any, List, Optional


# ==================================================
# SAFE ACCESS
# ==================================================
def safe_get(data: Dict[str, Any], key: str, default=None):
    return data.get(key, default) if isinstance(data, dict) else default


# ==================================================
# DESIGN SUMMARY
# ==================================================
def summarize_design(design: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "components": len(design.get("components", [])),
        "nets": len(design.get("nets", [])),
        "routes": len(design.get("routes", [])),
        "placed": len(design.get("layout", {})),
        "has_drc": "drc" in design
    }


# ==================================================
# COMPONENT UTILITIES
# ==================================================
def get_component(design: Dict[str, Any], ref: str) -> Optional[Dict[str, Any]]:
    for c in design.get("components", []):
        if c.get("ref") == ref:
            return c
    return None


def list_components(design: Dict[str, Any]) -> List[str]:
    return [c.get("ref") for c in design.get("components", [])]


# ==================================================
# NET UTILITIES
# ==================================================
def list_nets(design: Dict[str, Any]) -> List[str]:
    return [n.get("name") for n in design.get("nets", [])]


def get_net_connections(design: Dict[str, Any], net_name: str) -> List[str]:
    for n in design.get("nets", []):
        if n.get("name") == net_name:
            return n.get("connections", [])
    return []


# ==================================================
# POWER / SIGNAL ANALYSIS
# ==================================================
def find_power_nets(design: Dict[str, Any]) -> List[str]:
    power_keywords = ["vcc", "gnd", "power", "vin", "vout"]

    power_nets = []
    for net in design.get("nets", []):
        name = net.get("name", "").lower()
        if any(k in name for k in power_keywords):
            power_nets.append(net.get("name"))

    return power_nets


def find_signal_nets(design: Dict[str, Any]) -> List[str]:
    power = set(find_power_nets(design))
    return [n for n in list_nets(design) if n not in power]


# ==================================================
# LAYOUT UTILITIES
# ==================================================
def get_component_position(design: Dict[str, Any], ref: str):
    layout = design.get("layout", {})
    return layout.get(ref)


def get_unplaced_components(design: Dict[str, Any]) -> List[str]:
    layout = design.get("layout", {})
    return [
        c.get("ref")
        for c in design.get("components", [])
        if c.get("ref") not in layout
    ]


# ==================================================
# ROUTING UTILITIES
# ==================================================
def get_routes_for_net(design: Dict[str, Any], net_name: str):
    return [
        r for r in design.get("routes", [])
        if r.get("net") == net_name
    ]


def get_unrouted_nets(design: Dict[str, Any]) -> List[str]:
    routed = {r.get("net") for r in design.get("routes", [])}
    return [
        n.get("name")
        for n in design.get("nets", [])
        if n.get("name") not in routed
    ]


# ==================================================
# DRC UTILITIES
# ==================================================
def summarize_drc(design: Dict[str, Any]) -> Dict[str, Any]:
    drc = design.get("drc", [])

    summary = {
        "total": len(drc),
        "errors": 0,
        "warnings": 0
    }

    for issue in drc:
        level = issue.get("level", "error").lower()
        if level == "warning":
            summary["warnings"] += 1
        else:
            summary["errors"] += 1

    return summary


def get_drc_issues_by_type(design: Dict[str, Any]) -> Dict[str, int]:
    drc = design.get("drc", [])

    result = {}

    for issue in drc:
        t = issue.get("type", "unknown")
        result[t] = result.get(t, 0) + 1

    return result


# ==================================================
# DESIGN VALIDATION
# ==================================================
def is_design_valid(design: Dict[str, Any]) -> bool:
    if not design:
        return False

    if "components" not in design:
        return False

    if "nets" not in design:
        return False

    return True


# ==================================================
# GRAPH INSIGHTS
# ==================================================
def get_connectivity_map(design: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Net → components mapping
    """
    mapping = {}

    for net in design.get("nets", []):
        mapping[net.get("name")] = net.get("connections", [])

    return mapping


def get_component_degree(design: Dict[str, Any]) -> Dict[str, int]:
    """
    How many connections each component has
    """
    degree = {}

    for net in design.get("nets", []):
        for conn in net.get("connections", []):
            ref = conn.split(":")[0]
            degree[ref] = degree.get(ref, 0) + 1

    return degree


# ==================================================
# DEBUG TOOL
# ==================================================
def debug_design(design: Dict[str, Any]):
    print("\n===== DESIGN DEBUG =====")
    print("Components:", len(design.get("components", [])))
    print("Nets:", len(design.get("nets", [])))
    print("Routes:", len(design.get("routes", [])))
    print("DRC Issues:", len(design.get("drc", [])))
    print("========================\n")
  
