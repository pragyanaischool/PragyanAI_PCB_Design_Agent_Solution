# rag/vector_store.py

from typing import List, Dict, Any, Optional
import json
from pathlib import Path


class VectorStore:
    """
    Lightweight in-memory vector store (no embeddings yet).
    Designed to be easily upgraded to FAISS / Chroma later.
    """

    def __init__(self):
        self.data: List[Dict[str, Any]] = []

    # --------------------------------------------------
    # ADD METHODS
    # --------------------------------------------------
    def add(self, text: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Add a single document
        """
        if not text:
            return

        doc = {
            "text": text.strip(),
            "metadata": metadata or {}
        }

        if doc not in self.data:
            self.data.append(doc)

    def add_many(self, docs: List[Dict[str, Any]]):
        """
        Add multiple documents
        """
        for d in docs:
            self.add(d.get("text"), d.get("metadata"))

    # --------------------------------------------------
    # SEARCH
    # --------------------------------------------------
    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_meta: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Simple similarity search using token overlap
        """

        if not query:
            return []

        query_tokens = set(query.lower().split())

        scored = []

        for d in self.data:
            text = d["text"].lower()
            tokens = set(text.split())

            score = len(query_tokens & tokens)

            # Apply metadata filter if provided
            if filter_meta:
                if not all(
                    d["metadata"].get(k) == v
                    for k, v in filter_meta.items()
                ):
                    continue

            if score > 0:
                scored.append((score, d))

        # Sort by score (descending)
        scored.sort(key=lambda x: x[0], reverse=True)

        return [d for _, d in scored[:top_k]]

    # --------------------------------------------------
    # PERSISTENCE
    # --------------------------------------------------
    def save(self, path: Path):
        """
        Save store to disk
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def load(self, path: Path):
        """
        Load store from disk
        """
        if not path.exists():
            return

        with open(path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    # --------------------------------------------------
    # UTILITIES
    # --------------------------------------------------
    def clear(self):
        self.data = []

    def size(self) -> int:
        return len(self.data)

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return f"<VectorStore size={len(self.data)}>"

    # --------------------------------------------------
    # DEBUG
    # --------------------------------------------------
    def debug_print(self, n: int = 5):
        """
        Print first N entries
        """
        for d in self.data[:n]:
            print(d)


# --------------------------------------------------
# QUICK TEST
# --------------------------------------------------
if __name__ == "__main__":
    store = VectorStore()

    store.add("R1 is a 10k resistor", {"type": "component"})
    store.add("C1 is a capacitor", {"type": "component"})
    store.add("Net VCC connects R1 and C1", {"type": "net"})

    results = store.search("resistor")

    print("Results:")
    for r in results:
        print(r)

    # Save & load test
    path = Path("test_store.json")
    store.save(path)

    new_store = VectorStore()
    new_store.load(path)

    print("Loaded:", new_store)
  
