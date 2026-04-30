# rag/ingestion.py

from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import csv

from rag.vector_store import VectorStore


# ==================================================
# DESIGN → DOCUMENTS
# ==================================================
def design_to_docs(design: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert PCB design → RAG-friendly documents
    """

    docs: List[Dict[str, Any]] = []

    # ------------------------------
    # COMPONENTS
    # ------------------------------
    for c in design.get("components", []):
        ref = c.get("ref", "")
        value = c.get("value", "")
        footprint = c.get("footprint", "")

        docs.append({
            "text": f"{ref} is a {value} with footprint {footprint}",
            "metadata": {"type": "component", "ref": ref}
        })

    # ------------------------------
    # NETS
    # ------------------------------
    for n in design.get("nets", []):
        name = n.get("name", "")
        conns = ",".join(n.get("connections", []))

        docs.append({
            "text": f"Net {name} connects {conns}",
            "metadata": {"type": "net", "name": name}
        })

    # ------------------------------
    # LAYOUT
    # ------------------------------
    layout = design.get("layout", {})
    for ref, pos in layout.items():
        docs.append({
            "text": f"{ref} placed at ({pos.get('x')},{pos.get('y')})",
            "metadata": {"type": "layout", "ref": ref}
        })

    # ------------------------------
    # ROUTES
    # ------------------------------
    for r in design.get("routes", []):
        net = r.get("net", "")
        path = r.get("path", [])

        docs.append({
            "text": f"Route for net {net} follows {path}",
            "metadata": {"type": "route", "net": net}
        })

    # ------------------------------
    # DRC
    # ------------------------------
    for err in design.get("drc", []):
        docs.append({
            "text": f"DRC issue: {err}",
            "metadata": {"type": "drc"}
        })

    return docs


# ==================================================
# FILE → DOCUMENTS
# ==================================================
def load_json_docs(path: Path) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    docs = []

    if isinstance(data, list):
        for d in data:
            docs.append({
                "text": d.get("text", ""),
                "metadata": d.get("metadata", {})
            })

    return docs


def load_csv_docs(path: Path) -> List[Dict[str, Any]]:
    docs = []

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            text = " ".join([str(v) for v in row.values()])
            docs.append({
                "text": text,
                "metadata": {"type": "csv_row"}
            })

    return docs


def load_text_file(path: Path) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Simple chunking
    chunks = content.split("\n")

    return [
        {"text": chunk.strip(), "metadata": {"type": "text"}}
        for chunk in chunks if chunk.strip()
    ]


# ==================================================
# GENERIC FILE LOADER
# ==================================================
def load_documents(path: Path) -> List[Dict[str, Any]]:
    suffix = path.suffix.lower()

    if suffix == ".json":
        return load_json_docs(path)

    if suffix == ".csv":
        return load_csv_docs(path)

    if suffix in [".txt", ".md"]:
        return load_text_file(path)

    return []


# ==================================================
# INGEST INTO VECTOR STORE
# ==================================================
def ingest_design(
    design: Dict[str, Any],
    store: VectorStore
) -> int:
    """
    Ingest PCB design into store
    """
    docs = design_to_docs(design)

    store.add_many(docs)

    return len(docs)


def ingest_file(
    path: Path,
    store: VectorStore
) -> int:
    docs = load_documents(path)

    store.add_many(docs)

    return len(docs)


def ingest_batch(
    paths: List[Path],
    store: VectorStore
) -> int:
    total = 0

    for p in paths:
        total += ingest_file(p, store)

    return total


# ==================================================
# FILTERED INGESTION
# ==================================================
def ingest_with_filter(
    docs: List[Dict[str, Any]],
    store: VectorStore,
    allowed_types: Optional[List[str]] = None
) -> int:
    """
    Only ingest selected doc types
    """

    filtered = []

    for d in docs:
        doc_type = d.get("metadata", {}).get("type")

        if not allowed_types or doc_type in allowed_types:
            filtered.append(d)

    store.add_many(filtered)

    return len(filtered)


# ==================================================
# DEBUG
# ==================================================
if __name__ == "__main__":
    from rag.vector_store import VectorStore

    store = VectorStore()

    sample_design = {
        "components": [{"ref": "R1", "value": "10k"}],
        "nets": [{"name": "SIG", "connections": ["R1:1"]}]
    }

    count = ingest_design(sample_design, store)

    print("Ingested:", count)
    print("Store size:", len(store))
