# scripts/ingest_rag.py

import json
from pathlib import Path
from typing import List

from utils.logger import get_module_logger

logger = get_module_logger(__name__)


# --------------------------------------------------
# SIMPLE VECTOR STORE (FAKE / PLACEHOLDER)
# Replace with FAISS / Chroma / Weaviate
# --------------------------------------------------
class SimpleVectorStore:

    def __init__(self):
        self.data = []

    def add(self, text: str, metadata: dict):
        self.data.append({"text": text, "metadata": metadata})

    def save(self, path: Path):
        with open(path, "w") as f:
            json.dump(self.data, f, indent=2)

    def load(self, path: Path):
        with open(path, "r") as f:
            self.data = json.load(f)


# --------------------------------------------------
# BUILD DOCUMENTS
# --------------------------------------------------
def design_to_docs(design: dict) -> List[dict]:
    docs = []

    # Components
    for comp in design.get("components", []):
        docs.append({
            "text": f"{comp['ref']} {comp.get('value')} {comp.get('footprint')}",
            "metadata": {"type": "component"}
        })

    # Nets
    for net in design.get("nets", []):
        docs.append({
            "text": f"{net['name']} connects {', '.join(net.get('connections', []))}",
            "metadata": {"type": "net"}
        })

    return docs


# --------------------------------------------------
# INGEST
# --------------------------------------------------
def ingest_designs(input_dir: Path, output_file: Path):
    store = SimpleVectorStore()

    files = list(input_dir.glob("*.json"))

    for f in files:
        try:
            with open(f, "r") as fp:
                design = json.load(fp)

            docs = design_to_docs(design)

            for d in docs:
                store.add(d["text"], d["metadata"])

        except Exception as e:
            logger.warning(f"Failed to ingest {f}: {e}")

    store.save(output_file)

    logger.info(f"RAG store saved: {output_file}")


# --------------------------------------------------
# RUN
# --------------------------------------------------
if __name__ == "__main__":
    ingest_designs(
        Path("data/samples"),
        Path("outputs/rag_store.json")
    )
  
