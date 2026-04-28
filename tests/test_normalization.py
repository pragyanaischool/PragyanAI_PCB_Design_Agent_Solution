# tests/test_normalization.py

import pytest

from normalization.normalize import normalize_design
from normalization.validator import validate_design
from normalization.schema import create_design


# --------------------------------------------------
# BASIC NORMALIZATION
# --------------------------------------------------
def test_basic_normalization():
    raw = {
        "components": [{"ref": " r1 "}],
        "nets": [{"name": "vcc", "connections": ["r1:1"]}]
    }

    clean = normalize_design(raw)

    assert clean["components"][0]["ref"] == "R1"
    assert clean["nets"][0]["name"] == "VCC"


# --------------------------------------------------
# PIN NORMALIZATION
# --------------------------------------------------
def test_pin_normalization():
    raw = {
        "components": [
            {"ref": "R1", "pins": "1, 2 ,3"}
        ],
        "nets": []
    }

    clean = normalize_design(raw)

    assert clean["components"][0]["pins"] == ["1", "2", "3"]


# --------------------------------------------------
# CONNECTION CLEANUP
# --------------------------------------------------
def test_connection_deduplication():
    raw = {
        "components": [{"ref": "R1"}],
        "nets": [
            {"name": "SIG", "connections": ["R1:1", "R1:1"]}
        ]
    }

    clean = normalize_design(raw)

    assert len(clean["nets"][0]["connections"]) == 1


# --------------------------------------------------
# FOOTPRINT ENRICHMENT
# --------------------------------------------------
def test_footprint_auto_assignment():
    raw = {
        "components": [{"ref": "R1", "value": "10k"}],
        "nets": []
    }

    clean = normalize_design(raw)

    assert clean["components"][0]["footprint"] != ""


# --------------------------------------------------
# LAYOUT NORMALIZATION
# --------------------------------------------------
def test_layout_snap_and_clamp():
    raw = {
        "components": [{"ref": "R1"}],
        "nets": [],
        "layout": {
            "R1": {"x": 10.7, "y": 20.3}
        }
    }

    clean = normalize_design(raw)

    assert isinstance(clean["layout"]["R1"]["x"], (int, float))


# --------------------------------------------------
# ROUTE NORMALIZATION
# --------------------------------------------------
def test_route_normalization():
    raw = {
        "components": [{"ref": "R1"}, {"ref": "R2"}],
        "nets": [{"name": "SIG", "connections": ["R1:1", "R2:1"]}],
        "routes": [
            {"net": "sig", "path": [(0.1, 0.2), (10.5, 20.7)]}
        ]
    }

    clean = normalize_design(raw)

    assert clean["routes"][0]["net"] == "SIG"
    assert len(clean["routes"][0]["path"]) == 2


# --------------------------------------------------
# SCHEMA VALIDATION (Pydantic)
# --------------------------------------------------
def test_schema_creation():
    raw = {
        "components": [{"ref": "R1"}],
        "nets": [{"name": "VCC", "connections": ["R1:1"]}]
    }

    clean = normalize_design(raw)
    design = create_design(clean)

    assert design.components[0].ref == "R1"


# --------------------------------------------------
# VALIDATOR SUCCESS
# --------------------------------------------------
def test_validator_pass():
    raw = {
        "components": [{"ref": "R1"}],
        "nets": [{"name": "VCC", "connections": ["R1:1"]}]
    }

    clean = normalize_design(raw)
    result = validate_design(clean)

    assert result["status"] == "PASS"


# --------------------------------------------------
# VALIDATOR FAIL (DUPLICATE)
# --------------------------------------------------
def test_validator_duplicate():
    raw = {
        "components": [{"ref": "R1"}, {"ref": "R1"}],
        "nets": [{"name": "VCC", "connections": ["R1:1"]}]
    }

    clean = normalize_design(raw)

    result = validate_design(clean)

    assert result["status"] == "FAIL"


# --------------------------------------------------
# INVALID CONNECTION FORMAT
# --------------------------------------------------
def test_invalid_connection():
    raw = {
        "components": [{"ref": "R1"}],
        "nets": [{"name": "SIG", "connections": ["INVALID"]}]
    }

    clean = normalize_design(raw)

    result = validate_design(clean)

    assert result["status"] == "FAIL"


# --------------------------------------------------
# EMPTY INPUT
# --------------------------------------------------
def test_empty_input():
    raw = {}

    with pytest.raises(Exception):
        normalize_design(raw)


# --------------------------------------------------
# LARGE INPUT
# --------------------------------------------------
def test_large_input():
    raw = {
        "components": [{"ref": f"R{i}"} for i in range(50)],
        "nets": [
            {"name": "BUS", "connections": [f"R{i}:1" for i in range(50)]}
        ]
    }

    clean = normalize_design(raw)

    assert len(clean["components"]) == 50
  
