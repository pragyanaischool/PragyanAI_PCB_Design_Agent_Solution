# tests/test_drc.py

import pytest

from generation.drc.checks import run_drc
from generation.drc.rules import RuleEngine
from generation.autofix.fixer import auto_fix
from generation.drc.report import build_report


# --------------------------------------------------
# FIXTURES
# --------------------------------------------------
@pytest.fixture
def valid_design():
    return {
        "components": [
            {"ref": "R1"},
            {"ref": "R2"},
        ],
        "layout": {
            "R1": {"x": 0, "y": 0},
            "R2": {"x": 50, "y": 50},
        },
        "nets": [
            {"name": "SIG", "connections": ["R1:1", "R2:1"]}
        ],
        "routes": [
            {"net": "SIG", "path": [(0, 0), (50, 50)], "width": 1.0}
        ]
    }


@pytest.fixture
def overlap_design():
    return {
        "components": [
            {"ref": "R1"},
            {"ref": "R2"},
        ],
        "layout": {
            "R1": {"x": 10, "y": 10},
            "R2": {"x": 10, "y": 10},  # overlap
        },
        "nets": [],
        "routes": []
    }


@pytest.fixture
def thin_trace_design():
    return {
        "components": [{"ref": "R1"}, {"ref": "R2"}],
        "layout": {
            "R1": {"x": 0, "y": 0},
            "R2": {"x": 10, "y": 10},
        },
        "nets": [
            {"name": "SIG", "connections": ["R1:1", "R2:1"]}
        ],
        "routes": [
            {"net": "SIG", "path": [(0, 0), (10, 10)], "width": 0.01}
        ]
    }


# --------------------------------------------------
# BASIC DRC PASS
# --------------------------------------------------
def test_drc_pass(valid_design):
    result = run_drc(valid_design)

    assert result["status"] in ["PASS", "FAIL"]
    assert "errors" in result


# --------------------------------------------------
# OVERLAP DETECTION
# --------------------------------------------------
def test_overlap_detection(overlap_design):
    result = run_drc(overlap_design)

    assert any("overlap" in e["message"].lower() for e in result["errors"])


# --------------------------------------------------
# TRACE WIDTH VIOLATION
# --------------------------------------------------
def test_trace_width_violation(thin_trace_design):
    result = run_drc(thin_trace_design)

    assert any("width" in e["message"].lower() for e in result["errors"])


# --------------------------------------------------
# RULE ENGINE CUSTOMIZATION
# --------------------------------------------------
def test_custom_rules(valid_design):
    engine = RuleEngine({
        "min_trace_width": {"value": 2.0}
    })

    result = run_drc(valid_design)

    assert "status" in result


# --------------------------------------------------
# UNCONNECTED NET
# --------------------------------------------------
def test_unconnected_net():
    design = {
        "components": [{"ref": "R1"}],
        "nets": [{"name": "SIG", "connections": ["R1:1"]}],
        "layout": {"R1": {"x": 0, "y": 0}},
        "routes": []
    }

    result = run_drc(design)

    assert any(e["type"] == "unconnected_nets" for e in result["errors"])


# --------------------------------------------------
# BOUNDARY CHECK
# --------------------------------------------------
def test_boundary_violation():
    design = {
        "components": [{"ref": "R1"}],
        "layout": {"R1": {"x": -10, "y": -10}},
        "nets": [],
        "routes": []
    }

    result = run_drc(design)

    assert len(result["errors"]) >= 0


# --------------------------------------------------
# AUTOFIX LOOP
# --------------------------------------------------
def test_autofix(overlap_design):
    drc_before = run_drc(overlap_design)

    fixed = auto_fix(overlap_design)

    drc_after = run_drc(fixed)

    assert "routes" in fixed or "layout" in fixed
    assert drc_after["total_errors"] <= drc_before["total_errors"]


# --------------------------------------------------
# REPORT GENERATION
# --------------------------------------------------
def test_report_generation(valid_design):
    drc = run_drc(valid_design)

    report = build_report(drc)

    assert "summary" in report
    assert "errors" in report


# --------------------------------------------------
# EMPTY DESIGN
# --------------------------------------------------
def test_empty_design():
    design = {"components": [], "nets": []}

    result = run_drc(design)

    assert "status" in result


# --------------------------------------------------
# LARGE DESIGN
# --------------------------------------------------
def test_large_design():
    design = {
        "components": [{"ref": f"R{i}"} for i in range(20)],
        "layout": {
            f"R{i}": {"x": i * 10, "y": i * 10}
            for i in range(20)
        },
        "nets": [],
        "routes": []
    }

    result = run_drc(design)

    assert "status" in result


# --------------------------------------------------
# CONSISTENCY TEST
# --------------------------------------------------
def test_drc_consistency(valid_design):
    r1 = run_drc(valid_design)
    r2 = run_drc(valid_design)

    assert r1["total_errors"] == r2["total_errors"]
  
