# enrichment/footprint_resolution.py

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.logger import get_module_logger

logger = get_module_logger(__name__)

# --------------------------------------------------
# LOAD DB
# --------------------------------------------------
DB_PATH = Path(__file__).parent / "db" / "footprints.json"


def _load_db() -> Dict[str, Any]:
    if not DB_PATH.exists():
        logger.warning("Footprint DB not found, using empty DB")
        return {}
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load footprint DB: {e}")
        return {}


FOOTPRINT_DB = _load_db()

# Simple in-process cache
_CACHE: Dict[str, str] = {}


# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def _norm(v: Any) -> str:
    return str(v or "").strip().lower()


def _norm_upper(v: Any) -> str:
    return str(v or "").strip().upper()


def _has_existing(fp: str) -> bool:
    return bool(_norm(fp))


def _kicad_prefix(fp: str) -> str:
    """
    Ensure KiCad-like library prefix if missing
    """
    if ":" in fp:
        return fp
    # naive library inference
    if fp.startswith("R_"):
        return f"Resistor_SMD:{fp}"
    if fp.startswith("C_"):
        return f"Capacitor_SMD:{fp}"
    if "QFP" in fp or "TQFP" in fp or "QFN" in fp:
        return f"Package_QFP:{fp}"
    if "SOT" in fp:
        return f"Package_TO_SOT_SMD:{fp}"
    return f"Generic:{fp}"


def _regex_match(val: str, patterns: Dict[str, str]) -> Optional[str]:
    """
    Try regex-based mapping from DB["patterns"]
    """
    for pattern, fp in patterns.items():
        try:
            if re.search(pattern, val):
                return fp
        except re.error:
            continue
    return None


def _exact_lookup(val: str) -> Optional[str]:
    """
    Direct lookup in DB (case-insensitive)
    """
    if not FOOTPRINT_DB:
        return None

    # exact key
    if val in FOOTPRINT_DB:
        return FOOTPRINT_DB[val]

    # try normalized keys
    for k, v in FOOTPRINT_DB.items():
        if _norm(k) == val:
            return v

    return None


def _partial_lookup(val: str) -> Optional[str]:
    """
    Partial / contains matching
    """
    for k, v in FOOTPRINT_DB.items():
        if _norm(k) in val:
            return v
    return None


def _infer_from_package(text: str) -> Optional[str]:
    """
    Detect package hints like TQFP-32, QFN-48, SOT-23, 0805, 0603
    """
    t = _norm_upper(text)

    # QFP / TQFP / QFN
    m = re.search(r"(T?QFP[-_ ]?\d+)", t)
    if m:
        return _kicad_prefix(m.group(1).replace(" ", ""))

    m = re.search(r"(QFN[-_ ]?\d+)", t)
    if m:
        return _kicad_prefix(m.group(1).replace(" ", ""))

    # SOT
    m = re.search(r"(SOT[-_ ]?\d+)", t)
    if m:
        return _kicad_prefix(m.group(1).replace(" ", ""))

    # 0402 / 0603 / 0805 / 1206
    m = re.search(r"(0402|0603|0805|1206)", t)
    if m:
        code = m.group(1)
        # decide R or C later
        return code

    return None


def _infer_passive(val: str, package_hint: Optional[str]) -> Optional[str]:
    """
    Infer resistor/capacitor footprints
    """
    v = _norm(val)

    # Decide type
    is_res = ("ohm" in v) or ("k" in v) or ("r" in v and any(ch.isdigit() for ch in v))
    is_cap = ("f" in v) or ("uf" in v) or ("nf" in v) or ("pf" in v)

    # default sizes
    size = package_hint or "0805"

    if size in {"0402", "0603", "0805", "1206"}:
        if is_res:
            return f"Resistor_SMD:R_{size}"
        if is_cap:
            return f"Capacitor_SMD:C_{size}"

    # fallback
    if is_res:
        return "Resistor_SMD:R_0805"
    if is_cap:
        return "Capacitor_SMD:C_0603"

    return None


def _score_match(val: str, candidate: str) -> int:
    """
    Lightweight scoring: longer overlap wins
    """
    v = set(val.split())
    c = set(_norm(candidate).split())
    return len(v.intersection(c))


# --------------------------------------------------
# RESOLVE SINGLE COMPONENT
# --------------------------------------------------
def _resolve_one(comp: Dict[str, Any]) -> str:
    ref = comp.get("ref", "")
    value = _norm(comp.get("value"))
    footprint = comp.get("footprint", "")

    # 1) Keep existing
    if _has_existing(footprint):
        return _kicad_prefix(footprint)

    # Cache
    cache_key = value
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    # 2) Exact DB
    fp = _exact_lookup(value)
    if fp:
        _CACHE[cache_key] = _kicad_prefix(fp)
        return _CACHE[cache_key]

    # 3) Partial DB
    fp = _partial_lookup(value)
    if fp:
        _CACHE[cache_key] = _kicad_prefix(fp)
        return _CACHE[cache_key]

    # 4) Regex patterns in DB (optional section)
    patterns = FOOTPRINT_DB.get("_patterns", {})
    if isinstance(patterns, dict):
        fp = _regex_match(value, patterns)
        if fp:
            _CACHE[cache_key] = _kicad_prefix(fp)
            return _CACHE[cache_key]

    # 5) Package inference
    pkg = _infer_from_package(value)

    # 6) Passive inference
    fp = _infer_passive(value, pkg)
    if fp:
        _CACHE[cache_key] = fp
        return fp

    # 7) If pkg is explicit (e.g., TQFP-32)
    if pkg and ":" in pkg:
        _CACHE[cache_key] = pkg
        return pkg

    # 8) Fallback scoring against DB keys
    best = None
    best_score = 0
    for k, v in FOOTPRINT_DB.items():
        if k.startswith("_"):
            continue
        s = _score_match(value, k)
        if s > best_score:
            best = v
            best_score = s

    if best:
        _CACHE[cache_key] = _kicad_prefix(best)
        return _CACHE[cache_key]

    # 9) Final fallback
    logger.warning(f"No footprint match for {ref} ({value}), using UNKNOWN")
    return "Generic:UNKNOWN"


# --------------------------------------------------
# MAIN API
# --------------------------------------------------
def resolve_footprints(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Assign footprints to all components
    """

    logger.info("Starting footprint resolution")

    for comp in components:
        try:
            fp = _resolve_one(comp)
            comp["footprint"] = fp
        except Exception as e:
            logger.warning(f"Footprint resolution failed for {comp}: {e}")
            comp["footprint"] = "Generic:UNKNOWN"

    logger.info("Footprint resolution complete")
    return components


# --------------------------------------------------
# BULK (WITH STATS)
# --------------------------------------------------
def resolve_with_stats(components: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Resolve and return stats
    """
    total = len(components)
    unknown = 0

    resolve_footprints(components)

    for c in components:
        if c.get("footprint") == "Generic:UNKNOWN":
            unknown += 1

    return {
        "total": total,
        "unknown": unknown,
        "coverage": (total - unknown) / max(total, 1)
    }


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample = [
        {"ref": "R1", "value": "10k"},
        {"ref": "C1", "value": "100nF"},
        {"ref": "U1", "value": "ATmega328P TQFP-32"},
        {"ref": "Q1", "value": "SOT-23 MOSFET"},
        {"ref": "X1", "value": "UnknownPart"},
    ]

    comps = resolve_footprints(sample)

    for c in comps:
        print(c)

    print(resolve_with_stats(sample))
  
