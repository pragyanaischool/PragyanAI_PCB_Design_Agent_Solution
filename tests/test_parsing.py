# tests/test_parsing.py

import json
import pytest
from pathlib import Path

from parsing.router import parse_input
from parsing.csv_parser import parse_csv
from parsing.json_parser import parse_json
from parsing.kicad_parser import parse_kicad
from parsing.altium_parser import parse_altium


# --------------------------------------------------
# FIXTURES
# --------------------------------------------------
@pytest.fixture
def sample_json(tmp_path):
    file = tmp_path / "test.json"
    file.write_text(json.dumps({
        "components": [{"ref": "R1"}],
        "nets": [{"name": "VCC", "connections": ["R1:1"]}]
    }))
    return file


@pytest.fixture
def sample_csv(tmp_path):
    comp = tmp_path / "components.csv"
    nets = tmp_path / "nets.csv"

    comp.write_text("""ref,value,footprint,pins
R1,10k,R_0805,"1,2"
""")

    nets.write_text("""net,connections
VCC,"R1:1"
""")

    return comp, nets


@pytest.fixture
def sample_kicad(tmp_path):
    file = tmp_path / "test.kicad_sch"

    file.write_text("""
    (kicad_sch
      (symbol (property "Reference" "R1") (property "Value" "10k"))
      (net (code 1) (name "VCC"))
    )
    """)

    return file


@pytest.fixture
def sample_altium(tmp_path):
    file = tmp_path / "test.xml"

    file.write_text("""
    <Project>
      <Components>
        <Component RefDes="R1" Value="10k" />
      </Components>
    </Project>
    """)

    return file


# --------------------------------------------------
# JSON PARSER
# --------------------------------------------------
def test_parse_json(sample_json):
    design = parse_json(sample_json)

    assert "components" in design
    assert "nets" in design
    assert design["components"][0]["ref"] == "R1"


def test_parse_json_invalid(tmp_path):
    file = tmp_path / "bad.json"
    file.write_text("{ invalid json }")

    with pytest.raises(Exception):
        parse_json(file)


# --------------------------------------------------
# CSV PARSER
# --------------------------------------------------
def test_parse_csv(sample_csv):
    comp, nets = sample_csv

    design = parse_csv(comp, nets)

    assert len(design["components"]) == 1
    assert design["components"][0]["ref"] == "R1"
    assert design["nets"][0]["name"] == "VCC"


# --------------------------------------------------
# KICAD PARSER
# --------------------------------------------------
def test_parse_kicad(sample_kicad):
    design = parse_kicad(sample_kicad)

    assert "components" in design
    assert len(design["components"]) >= 1


# --------------------------------------------------
# ALTIUM PARSER
# --------------------------------------------------
def test_parse_altium(sample_altium):
    design = parse_altium(sample_altium)

    assert "components" in design
    assert design["components"][0]["ref"] == "R1"


# --------------------------------------------------
# ROUTER (AUTO DETECTION)
# --------------------------------------------------
def test_router_json(sample_json):
    design = parse_input(sample_json)

    assert design["components"][0]["ref"] == "R1"


def test_router_csv(sample_csv):
    design = parse_input(sample_csv)

    assert design["nets"][0]["name"] == "VCC"


def test_router_kicad(sample_kicad):
    design = parse_input(sample_kicad)

    assert "components" in design


def test_router_altium(sample_altium):
    design = parse_input(sample_altium)

    assert "components" in design


# --------------------------------------------------
# EDGE CASES
# --------------------------------------------------
def test_missing_file():
    with pytest.raises(FileNotFoundError):
        parse_input("non_existent.json")


def test_invalid_format(tmp_path):
    file = tmp_path / "file.txt"
    file.write_text("random text")

    with pytest.raises(ValueError):
        parse_input(file)


def test_empty_design(tmp_path):
    file = tmp_path / "empty.json"
    file.write_text("{}")

    design = parse_input(file)

    assert "components" in design
    assert "nets" in design


# --------------------------------------------------
# NET EXTRACTION FALLBACK
# --------------------------------------------------
def test_kicad_net_fallback(sample_kicad):
    design = parse_input(sample_kicad)

    assert "nets" in design


# --------------------------------------------------
# MULTIPLE INPUTS
# --------------------------------------------------
def test_multiple_files(tmp_path):
    files = []

    for i in range(3):
        f = tmp_path / f"test_{i}.json"
        f.write_text(json.dumps({
            "components": [{"ref": f"R{i}"}],
            "nets": []
        }))
        files.append(f)

    results = [parse_input(f) for f in files]

    assert len(results) == 3
  
