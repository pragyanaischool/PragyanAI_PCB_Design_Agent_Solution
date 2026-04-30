# rag/vector_store.py

from typing import List, Dict, Any, Optional
from pathlib import Path
import json


class VectorStore:
    """
    Lightweight Vector Store (Keyword-based)
    Upgrade-ready for embeddings (FAISS / Chroma)
    """

    def __init__(self):
        self.data: List[Dict[str, Any]] = []

    # --------------------------------------------------
    # ADD METHODS
    # --------------------------------------------------
    def add(self, text: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Add single document
        """
        if not text:
            return

        doc = {
            "text": text.strip(),
            "metadata": metadata or {}
        }

        # Avoid duplicates
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
        Keyword-based search with scoring
        """

        if not query:
            return []

        query_tokens = set(query.lower().split())
        scored_results = []

        for doc in self.data:
            text = doc["text"].lower()
            tokens = set(text.split())

            # Score: token overlap
            score = len(query_tokens & tokens)

            # Metadata filtering
            if filter_meta:
                if not all(
                    doc["metadata"].get(k) == v
                    for k, v in filter_meta.items()
                ):
                    continue

            if score > 0:
                scored_results.append((score, doc))

        # Sort by score (descending)
        scored_results.sort(key=lambda x: x[0], reverse=True)

        return [doc for _, doc in scored_results[:top_k]]

    # --------------------------------------------------
    # PERSISTENCE
    # --------------------------------------------------
    def save(self, path: Path):
        """
        Save vector store to disk
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def load(self, path: Path):
        """
        Load vector store from disk
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
        for d in self.data[:n]:
            print(d)


# --------------------------------------------------
# TEST
# --------------------------------------------------
if __name__ == "__main__":
    store = VectorStore()

    store.add("R1 is a 10k resistor", {"type": "component"})
    store.add("C1 is a capacitor", {"type": "component"})
    store.add("VCC connects R1 and C1", {"type": "net"})

    print("Search: resistor")
    results = store.search("resistor")

    for r in results:
        print(r)

    # Save & Load test
    test_path = Path("test_store.json")
    store.save(test_path)

    new_store = VectorStore()
    new_store.load(test_path)

    print("Loaded store:", new_store)
  
