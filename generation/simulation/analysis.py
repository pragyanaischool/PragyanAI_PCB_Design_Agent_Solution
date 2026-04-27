# simulation/analysis.py

from typing import Dict, Any, List
import math

from utils.logger import get_module_logger
from simulation.ngspice import simulate

logger = get_module_logger(__name__)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def parse_resistance(value: str) -> float:
    """
    Convert '10k', '1M', etc → numeric Ohms
    """
    if not value:
        return 0

    v = value.lower().strip()

    try:
        if "k" in v:
            return float(v.replace("k", "")) * 1e3
        elif "m" in v:
            return float(v.replace("m", "")) * 1e6
        else:
            return float(v)
    except:
        return 0


# --------------------------------------------------
# POWER ESTIMATION
# --------------------------------------------------
def estimate_power(design: Dict[str, Any], voltage: float = 5.0):
    """
    Rough DC power estimation
    """

    resistances = []

    for comp in design.get("components", []):
        val = comp.get("value", "")
        r = parse_resistance(val)
        if r > 0:
            resistances.append(r)

    if not resistances:
        return {"status": "unknown"}

    total_r = sum(resistances)

    try:
        current = voltage / total_r
        power = voltage * current
    except:
        return {"status": "error"}

    return {
        "total_resistance": total_r,
        "voltage": voltage,
        "current": current,
        "power": power
    }


# --------------------------------------------------
# SIGNAL FLOW
# --------------------------------------------------
def signal_flow(design: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Analyze net-level signal paths
    """

    flows = []

    for net in design.get("nets", []):
        flows.append({
            "net": net.get("name"),
            "connections": net.get("connections", [])
        })

    return flows


# --------------------------------------------------
# CONNECTIVITY CHECK
# --------------------------------------------------
def connectivity_health(design: Dict[str, Any]):
    """
    Detect isolated or weak connections
    """

    issues = []

    for net in design.get("nets", []):
        conns = net.get("connections", [])

        if len(conns) < 2:
            issues.append({
                "type": "WEAK_NET",
                "net": net.get("name"),
                "message": "Less than 2 connections"
            })

    return {
        "issues": issues,
        "healthy": len(issues) == 0
    }


# --------------------------------------------------
# THERMAL ESTIMATION
# --------------------------------------------------
def thermal_analysis(design: Dict[str, Any]):
    """
    Simple heat estimation (heuristic)
    """

    heat_sources = []

    keywords = ["mosfet", "cpu", "mcu", "regulator", "driver"]

    for comp in design.get("components", []):
        val = comp.get("value", "").lower()

        if any(k in val for k in keywords):
            heat_sources.append(comp["ref"])

    return {
        "heat_components": heat_sources,
        "count": len(heat_sources)
    }


# --------------------------------------------------
# DESIGN COMPLEXITY SCORE
# --------------------------------------------------
def complexity_score(design: Dict[str, Any]):
    """
    Score design complexity (0–100)
    """

    comp_count = len(design.get("components", []))
    net_count = len(design.get("nets", []))
    route_count = len(design.get("routes", []))

    score = min(100, comp_count * 2 + net_count * 3 + route_count)

    return {
        "score": score,
        "components": comp_count,
        "nets": net_count,
        "routes": route_count
    }


# --------------------------------------------------
# SIMULATION WRAPPER
# --------------------------------------------------
def run_simulation(design: Dict[str, Any]):
    try:
        sim = simulate(design)

        if sim.get("success"):
            return {
                "status": "success",
                "results": sim.get("parsed", {})
            }
        else:
            return {
                "status": "fallback",
                "message": sim.get("error", "simulation failed")
            }

    except Exception as e:
        logger.error(f"Simulation error: {e}")
        return {"status": "error", "message": str(e)}


# --------------------------------------------------
# FULL ANALYSIS PIPELINE
# --------------------------------------------------
def analyze_circuit(design: Dict[str, Any]) -> Dict[str, Any]:
    """
    Full circuit intelligence pipeline
    """

    logger.info("Running full circuit analysis")

    result = {}

    # 1. Simulation
    result["simulation"] = run_simulation(design)

    # 2. Power
    result["power"] = estimate_power(design)

    # 3. Signal flow
    result["signal_flow"] = signal_flow(design)

    # 4. Connectivity
    result["connectivity"] = connectivity_health(design)

    # 5. Thermal
    result["thermal"] = thermal_analysis(design)

    # 6. Complexity
    result["complexity"] = complexity_score(design)

    # 7. Overall health
    result["health"] = evaluate_design_health(result)

    return result


# --------------------------------------------------
# HEALTH SCORING
# --------------------------------------------------
def evaluate_design_health(analysis: Dict[str, Any]):
    """
    Combine metrics into health score
    """

    score = 100

    # Penalize connectivity issues
    if not analysis["connectivity"]["healthy"]:
        score -= 20

    # Penalize high heat
    if analysis["thermal"]["count"] > 3:
        score -= 15

    # Penalize high complexity
    if analysis["complexity"]["score"] > 80:
        score -= 10

    status = "GOOD"
    if score < 70:
        status = "MODERATE"
    if score < 50:
        status = "POOR"

    return {
        "score": score,
        "status": status
    }


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample = {
        "components": [
            {"ref": "R1", "value": "1k"},
            {"ref": "R2", "value": "2k"},
            {"ref": "U1", "value": "ATmega"},
        ],
        "nets": [
            {"name": "SIG", "connections": ["R1:1", "R2:1"]},
            {"name": "GND", "connections": ["R1:2"]},  # weak
        ],
        "routes": []
    }

    result = analyze_circuit(sample)

    from pprint import pprint
    pprint(result)
  
