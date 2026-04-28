# tests/test_routing.py

import pytest

from generation.routing.manhattan import auto_route as manhattan_route
from generation.routing.graph_router import graph_route
from generation.routing.autorouter import autoroute


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
        "layout": {
            "R1": {"x": 0, "y": 0},
            "R2": {"x": 10, "y": 10},
        },
        "nets": [
            {"name": "SIG", "connections": ["R1:1", "R2:1"]}
        ],
        "routes": []
    }


@pytest.fixture
def multi_net_design():
    return {
        "components": [
            {"ref": "U1"},
            {"ref": "R1"},
            {"ref": "C1"},
        ],
        "layout": {
            "U1": {"x": 0, "y": 0},
            "R1": {"x": 20, "y": 20},
            "C1": {"x": 40, "y": 40},
        },
        "nets": [
            {"name": "N1", "connections": ["U1:1", "R1:1"]},
            {"name": "N2", "connections": ["R1:2", "C1:1"]},
        ],
        "routes": []
    }


# --------------------------------------------------
# MANHATTAN ROUTER
# --------------------------------------------------
def test_manhattan_route(simple_design):
    routed = manhattan_route(simple_design)

    assert "routes" in routed
    assert len(routed["routes"]) > 0

    route = routed["routes"][0]
    assert "path" in route
    assert len(route["path"]) >= 2


# --------------------------------------------------
# GRAPH ROUTER (A*)
# --------------------------------------------------
def test_graph_router(simple_design):
    routed = graph_route(simple_design)

    assert len(routed["routes"]) > 0

    path = routed["routes"][0]["path"]

    # Path starts and ends correctly
    assert path[0] == (0, 0)
    assert path[-1] == (10, 10)


# --------------------------------------------------
# MULTI-NET ROUTING
# --------------------------------------------------
def test_multi_net_routing(multi_net_design):
    routed = autoroute(multi_net_design)

    assert len(routed["routes"]) >= 2


# --------------------------------------------------
# AUTOROUTER (HYBRID)
# --------------------------------------------------
def test_autorouter_hybrid(simple_design):
    routed = autoroute(simple_design, strategy="hybrid")

    assert "routes" in routed
    assert len(routed["routes"]) > 0


# --------------------------------------------------
# AUTOROUTER (FAST)
# --------------------------------------------------
def test_autorouter_fast(simple_design):
    routed = autoroute(simple_design, strategy="fast")

    assert len(routed["routes"]) > 0


# --------------------------------------------------
# AUTOROUTER (ADVANCED)
# --------------------------------------------------
def test_autorouter_advanced(simple_design):
    routed = autoroute(simple_design, strategy="advanced")

    assert len(routed["routes"]) > 0


# --------------------------------------------------
# ROUTE VALIDITY
# --------------------------------------------------
def test_route_validity(simple_design):
    routed = autoroute(simple_design)

    for route in routed["routes"]:
        path = route["path"]

        assert len(path) >= 2

        # Ensure no duplicate consecutive points
        for i in range(len(path) - 1):
            assert path[i] != path[i + 1]


# --------------------------------------------------
# NO LAYOUT CASE
# --------------------------------------------------
def test_no_layout():
    design = {
        "components": [{"ref": "R1"}],
        "nets": [{"name": "SIG", "connections": ["R1:1"]}]
    }

    routed = autoroute(design)

    assert routed["routes"] == []


# --------------------------------------------------
# INVALID NET CONNECTION
# --------------------------------------------------
def test_invalid_connection():
    design = {
        "components": [{"ref": "R1"}],
        "layout": {"R1": {"x": 0, "y": 0}},
        "nets": [
            {"name": "SIG", "connections": ["INVALID"]}
        ],
        "routes": []
    }

    routed = autoroute(design)

    assert "routes" in routed


# --------------------------------------------------
# RETRY MECHANISM
# --------------------------------------------------
def test_retry_mechanism(simple_design):
    routed = autoroute(simple_design, strategy="hybrid")

    assert len(routed["routes"]) > 0


# --------------------------------------------------
# ROUTE SMOOTHING
# --------------------------------------------------
def test_route_smoothing(simple_design):
    routed = autoroute(simple_design)

    route = routed["routes"][0]
    path = route["path"]

    # After smoothing, path should still be valid
    assert len(path) >= 2


# --------------------------------------------------
# LARGE DESIGN
# --------------------------------------------------
def test_large_routing():
    design = {
        "components": [{"ref": f"R{i}"} for i in range(10)],
        "layout": {
            f"R{i}": {"x": i * 10, "y": i * 10}
            for i in range(10)
        },
        "nets": [
            {
                "name": "BUS",
                "connections": [f"R{i}:1" for i in range(10)]
            }
        ],
        "routes": []
    }

    routed = autoroute(design)

    assert len(routed["routes"]) > 0


# --------------------------------------------------
# CONSISTENCY TEST
# --------------------------------------------------
def test_routing_consistency(simple_design):
    r1 = autoroute(simple_design)
    r2 = autoroute(simple_design)

    assert len(r1["routes"]) == len(r2["routes"])
  
