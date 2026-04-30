# rag/memory.py

from typing import List, Dict, Optional
from pathlib import Path
import json


# ==================================================
# MESSAGE STRUCTURE
# ==================================================
def create_message(role: str, content: str) -> Dict[str, str]:
    return {
        "role": role,
        "content": content.strip()
    }


# ==================================================
# CHAT MEMORY CLASS
# ==================================================
class ChatMemory:
    """
    Stores conversation history for RAG + LLM usage
    """

    def __init__(self, max_messages: int = 50):
        self.history: List[Dict[str, str]] = []
        self.max_messages = max_messages

    # --------------------------------------------------
    # ADD MESSAGE
    # --------------------------------------------------
    def add(self, role: str, content: str):
        msg = create_message(role, content)

        self.history.append(msg)

        # Trim memory
        if len(self.history) > self.max_messages:
            self.history = self.history[-self.max_messages:]

    # --------------------------------------------------
    # ADD USER + ASSISTANT PAIR
    # --------------------------------------------------
    def add_interaction(self, user: str, assistant: str):
        self.add("user", user)
        self.add("assistant", assistant)

    # --------------------------------------------------
    # GET RECENT HISTORY
    # --------------------------------------------------
    def get_recent(self, k: int = 5) -> List[Dict[str, str]]:
        return self.history[-k:]

    # --------------------------------------------------
    # FORMAT FOR LLM
    # --------------------------------------------------
    def to_text(self, k: int = 5) -> str:
        """
        Convert memory → prompt-friendly text
        """
        msgs = self.get_recent(k)

        return "\n".join(
            [f"{m['role']}: {m['content']}" for m in msgs]
        )

    # --------------------------------------------------
    # FORMAT AS CHAT MESSAGES (LLM API)
    # --------------------------------------------------
    def to_messages(self, k: int = 5) -> List[Dict[str, str]]:
        """
        Convert to OpenAI / Groq format
        """
        return self.get_recent(k)

    # --------------------------------------------------
    # SEARCH MEMORY (KEYWORD)
    # --------------------------------------------------
    def search(self, query: str) -> List[Dict[str, str]]:
        query = query.lower()

        return [
            m for m in self.history
            if query in m["content"].lower()
        ]

    # --------------------------------------------------
    # CLEAR MEMORY
    # --------------------------------------------------
    def clear(self):
        self.history = []

    # --------------------------------------------------
    # SAVE TO FILE
    # --------------------------------------------------
    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2)

    # --------------------------------------------------
    # LOAD FROM FILE
    # --------------------------------------------------
    def load(self, path: Path):
        if not path.exists():
            return

        with open(path, "r", encoding="utf-8") as f:
            self.history = json.load(f)

    # --------------------------------------------------
    # SIZE
    # --------------------------------------------------
    def __len__(self):
        return len(self.history)

    def __repr__(self):
        return f"<ChatMemory size={len(self.history)}>"
    

# ==================================================
# MEMORY MANAGER (OPTIONAL GLOBAL)
# ==================================================
class MemoryManager:
    """
    Manages multiple sessions (useful for multi-user apps)
    """

    def __init__(self):
        self.sessions: Dict[str, ChatMemory] = {}

    def get(self, session_id: str) -> ChatMemory:
        if session_id not in self.sessions:
            self.sessions[session_id] = ChatMemory()

        return self.sessions[session_id]

    def clear(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id].clear()


# ==================================================
# DEBUG TEST
# ==================================================
if __name__ == "__main__":
    mem = ChatMemory()

    mem.add("user", "What is R1?")
    mem.add("assistant", "R1 is a resistor")

    print(mem.to_text())

    mem.save(Path("memory.json"))

    new_mem = ChatMemory()
    new_mem.load(Path("memory.json"))

    print("Loaded:", new_mem)
  
