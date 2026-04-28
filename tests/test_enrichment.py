# tests/test_enrichment.py

import pytest

from normalization.normalize import normalize_design


# --------------------------------------------------
# FIXTURES
# --------------------------------------------------
@pytest.fixture
def base_design():
    return {
        "components": [
            {"ref": "R1", "value": "10k"},
            {"ref": "C1", "value": "100nF"},
        ],
        "nets": [
            {"name": "SIG", "connections": ["R1:1", "C1:1"]}
        ]
    }


# --------------------------------------------------
# FOOTPRINT RESOLUTION
# --------------------------------------------------
def test_footprint_resolution(base_design):
    clean = normalize_design(base_design)

    for comp in clean["components"]:
        assert "footprint" in comp
        assert comp["footprint"] != ""


# --------------------------------------------------
# PIN NORMALIZATION
# --------------------------------------------------
def test_pin_enrichment():
    design = {
        "components": [
            {"ref": "U1", "pins": "VCC,GND,PB0"}
        ],
        "nets": []
    }

    clean = normalize_design(design)

    assert clean["components"][0]["pins"] == ["VCC", "GND", "PB0"]


# --------------------------------------------------
# CONNECTION NORMALIZATION
# --------------------------------------------------
def test_connection_enrichment():
    design = {
        "components": [{"ref": "R1"}],
        "nets": [
            {"name": "sig", "connections": [" r1 : 1 "]}
        ]
    }

    clean = normalize_design(design)

    assert clean["nets"][0]["connections"][0] == "R1:1"


# --------------------------------------------------
# DUPLICATE REMOVAL
# --------------------------------------------------
def test_duplicate_connections():
    design = {
        "components": [{"ref": "R1"}],
        "nets": [
            {"name": "SIG", "connections": ["R1:1", "R1:1"]}
        ]
    }

    clean = normalize_design(design)

    assert len(clean["nets"][0]["connections"]) == 1


# --------------------------------------------------
# METADATA PRESERVATION
# --------------------------------------------------
def test_metadata_preserved():
    design = {
        "components": [
            {"ref": "R1", "metadata": {"tolerance": "5%"}}
        ],
        "nets": []
    }

    clean = normalize_design(design)

    assert "metadata" in clean["components"][0]
    assert clean["components"][0]["metadata"]["tolerance"] == "5%"


# --------------------------------------------------
# AUTO FOOTPRINT BASED ON VALUE
# --------------------------------------------------
def test_value_based_footprint():
    design = {
        "components": [
            {"ref": "R1", "value": "10k"},
            {"ref": "C1", "value": "100nF"},
        ],
        "nets": []
    }

    clean = normalize_design(design)

    r_fp = clean["components"][0]["footprint"]
    c_fp = clean["components"][1]["footprint"]

    assert "R_" in r_fp or "Resistor" in r_fp
    assert "C_" in c_fp or "Capacitor" in c_fp


# --------------------------------------------------
# EMPTY COMPONENT VALUE
# --------------------------------------------------
def test_missing_value():
    design = {
        "components": [{"ref": "R1"}],
        "nets": []
    }

    clean = normalize_design(design)

    assert clean["components"][0]["value"] == ""


# --------------------------------------------------
# MIXED INPUT FORMATS
# --------------------------------------------------
def test_mixed_input_formats():
    design = {
        "components": [
            {"ref": "R1", "pins": ["1", "2"]},
            {"ref": "C1", "pins": "1,2"},
        ],
        "nets": []
    }

    clean = normalize_design(design)

    assert clean["components"][0]["pins"] == ["1", "2"]
    assert clean["components"][1]["pins"] == ["1", "2"]


# --------------------------------------------------
# INVALID PIN FORMAT
# --------------------------------------------------
def test_invalid_pin_format():
    design = {
        "components": [{"ref": "U1", "pins": None}],
        "nets": []
    }

    clean = normalize_design(design)

    assert clean["components"][0]["pins"] == []


# --------------------------------------------------
# LARGE DESIGN ENRICHMENT
# --------------------------------------------------
def test_large_enrichment():
    design = {
        "components": [{"ref": f"R{i}", "value": "10k"} for i in range(20)],
        "nets": []
    }

    clean = normalize_design(design)

    assert len(clean["components"]) == 20

    for comp in clean["components"]:
        assert comp["footprint"] != ""


# --------------------------------------------------
# CONSISTENCY
# --------------------------------------------------
def test_enrichment_consistency(base_design):
    c1 = normalize_design(base_design)
    c2 = normalize_design(base_design)

    assert c1 == c2
  
