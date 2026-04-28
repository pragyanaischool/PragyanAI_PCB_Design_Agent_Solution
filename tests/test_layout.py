# tests/test_layout.py

import pytest

from generation.layout.auto_place import auto_place
from generation.layout.constraints import apply_constraints


# --------------------------------------------------
# FIXTURES
# --------------------------------------------------
@pytest.fixture
def simple_design():
    return {
        "components": [
            {"ref": "R1"},
            {"ref": "R2"},
        ],
        "nets": []
    }


@pytest.fixture
def power_design():
    return {
        "components": [
            {"ref": "U1", "value": "ATmega"},
            {"ref": "U2", "value": "7805"},  # power
        ],
        "nets": []
    }


@pytest.fixture
def thermal_design():
    return {
        "components": [
            {"ref": "Q1", "value": "MOSFET"},
            {"ref": "Q2", "value": "MOSFET"},
        ],
        "nets": []
    }


# --------------------------------------------------
# BASIC PLACEMENT
# --------------------------------------------------
def test_auto_place_basic(simple_design):
    result = auto_place(simple_design)

    assert "layout" in result
    assert len(result["layout"]) == 2
    assert "R1" in result["layout"]


# --------------------------------------------------
# UNIQUE POSITIONS
# --------------------------------------------------
def test_no_overlap(simple_design):
    result = auto_place(simple_design)

    positions = list(result["layout"].values())

    assert positions[0] != positions[1]


# --------------------------------------------------
# BOUNDARY CHECK
# --------------------------------------------------
def test_boundary_enforcement(simple_design):
    design = auto_place(simple_design)
    design = apply_constraints(design)

    for pos in design["layout"].values():
        assert pos["x"] >= 0
        assert pos["y"] >= 0


# --------------------------------------------------
# POWER PLACEMENT
# --------------------------------------------------
def test_power_components_near_origin(power_design):
    design = auto_place(power_design)
    design = apply_constraints(design, {"power_zone": True})

    power_pos = design["layout"]["U2"]

    assert power_pos["x"] <= 10
    assert power_pos["y"] <= 10


# --------------------------------------------------
# THERMAL SPACING
# --------------------------------------------------
def test_thermal_spacing(thermal_design):
    design = auto_place(thermal_design)
    design = apply_constraints(design, {"thermal": True})

    pos1 = design["layout"]["Q1"]
    pos2 = design["layout"]["Q2"]

    assert abs(pos1["x"] - pos2["x"]) > 0


# --------------------------------------------------
# KEEP-OUT ZONE
# --------------------------------------------------
def test_keepout_zone(simple_design):
    design = auto_place(simple_design)

    keepouts = [(0, 0, 20, 20)]

    design = apply_constraints(design, {"keepouts": keepouts})

    for pos in design["layout"].values():
        assert not (0 <= pos["x"] <= 20 and 0 <= pos["y"] <= 20)


# --------------------------------------------------
# GROUPING (NET CONNECTIVITY)
# --------------------------------------------------
def test_grouping():
    design = {
        "components": [
            {"ref": "U1"},
            {"ref": "R1"},
        ],
        "nets": [
            {"name": "SIG", "connections": ["U1:1", "R1:1"]}
        ]
    }

    design = auto_place(design)
    design = apply_constraints(design, {"grouping": True})

    pos1 = design["layout"]["U1"]
    pos2 = design["layout"]["R1"]

    assert abs(pos1["x"] - pos2["x"]) < 50  # closer


# --------------------------------------------------
# ALIGNMENT
# --------------------------------------------------
def test_alignment(simple_design):
    design = auto_place(simple_design)
    design = apply_constraints(design, {"align": "x"})

    xs = [pos["x"] for pos in design["layout"].values()]

    assert len(set(xs)) == 1


# --------------------------------------------------
# EMPTY DESIGN
# --------------------------------------------------
def test_empty_design():
    design = {"components": [], "nets": []}

    result = auto_place(design)

    assert "layout" in result
    assert len(result["layout"]) == 0


# --------------------------------------------------
# LARGE DESIGN
# --------------------------------------------------
def test_large_design():
    design = {
        "components": [{"ref": f"R{i}"} for i in range(50)],
        "nets": []
    }

    result = auto_place(design)

    assert len(result["layout"]) == 50


# --------------------------------------------------
# STABILITY TEST (OPTIONAL)
# --------------------------------------------------
def test_repeatability(simple_design):
    result1 = auto_place(simple_design)
    result2 = auto_place(simple_design)

    # Allow slight variation but structure must exist
    assert set(result1["layout"].keys()) == set(result2["layout"].keys())
  
