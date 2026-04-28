# tests/test_rag.py

import json
import pytest
from pathlib import Path

from scripts.ingest_rag import design_to_docs, SimpleVectorStore


# --------------------------------------------------
# FIXTURES
# --------------------------------------------------
@pytest.fixture
def sample_design():
    return {
        "components": [
            {"ref": "R1", "value": "10k", "footprint": "R_0805"},
            {"ref": "C1", "value": "100nF"},
        ],
        "nets": [
            {"name": "VCC", "connections": ["R1:1", "C1:1"]},
            {"name": "GND", "connections": ["R1:2", "C1:2"]},
        ]
    }


# --------------------------------------------------
# DOCUMENT GENERATION
# --------------------------------------------------
def test_design_to_docs(sample_design):
    docs = design_to_docs(sample_design)

    assert len(docs) > 0
    assert any("R1" in d["text"] for d in docs)


# --------------------------------------------------
# VECTOR STORE ADD
# --------------------------------------------------
def test_vector_store_add():
    store = SimpleVectorStore()

    store.add("test text", {"type": "component"})

    assert len(store.data) == 1
    assert store.data[0]["text"] == "test text"


# --------------------------------------------------
# SAVE + LOAD
# --------------------------------------------------
def test_vector_store_save_load(tmp_path):
    store = SimpleVectorStore()

    store.add("R1 10k", {"type": "component"})

    file = tmp_path / "store.json"

    store.save(file)

    new_store = SimpleVectorStore()
    new_store.load(file)

    assert len(new_store.data) == 1
    assert new_store.data[0]["text"] == "R1 10k"


# --------------------------------------------------
# INGEST MULTIPLE DESIGNS
# --------------------------------------------------
def test_ingest_multiple(tmp_path):
    input_dir = tmp_path / "samples"
    input_dir.mkdir()

    for i in range(3):
        file = input_dir / f"d{i}.json"
        file.write_text(json.dumps({
            "components": [{"ref": f"R{i}"}],
            "nets": []
        }))

    store = SimpleVectorStore()

    for f in input_dir.glob("*.json"):
        with open(f) as fp:
            design = json.load(fp)

        docs = design_to_docs(design)

        for d in docs:
            store.add(d["text"], d["metadata"])

    assert len(store.data) >= 3


# --------------------------------------------------
# EMPTY DESIGN
# --------------------------------------------------
def test_empty_design():
    docs = design_to_docs({"components": [], "nets": []})

    assert isinstance(docs, list)
    assert len(docs) == 0


# --------------------------------------------------
# INVALID DESIGN STRUCTURE
# --------------------------------------------------
def test_invalid_design():
    design = {"invalid": "data"}

    docs = design_to_docs(design)

    assert isinstance(docs, list)


# --------------------------------------------------
# SIMPLE RETRIEVAL (SIMULATION)
# --------------------------------------------------
def test_simple_retrieval():
    store = SimpleVectorStore()

    store.add("R1 resistor 10k", {"type": "component"})
    store.add("C1 capacitor 100nF", {"type": "component"})

    # Simulate naive retrieval
    query = "resistor"

    results = [d for d in store.data if query in d["text"]]

    assert len(results) == 1
    assert "R1" in results[0]["text"]


# --------------------------------------------------
# METADATA CHECK
# --------------------------------------------------
def test_metadata_integrity(sample_design):
    docs = design_to_docs(sample_design)

    for d in docs:
        assert "metadata" in d
        assert "type" in d["metadata"]


# --------------------------------------------------
# CONSISTENCY TEST
# --------------------------------------------------
def test_rag_consistency(sample_design):
    docs1 = design_to_docs(sample_design)
    docs2 = design_to_docs(sample_design)

    assert docs1 == docs2
  
