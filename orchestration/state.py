# orchestration/state.py

from typing import Dict, Any, List, Optional
from datetime import datetime
import copy


class PCBState(dict):
    """
    Shared state across all agents in the PCB multi-agent system.

    Features:
    - Centralized data store
    - Logging & debugging
    - Error tracking
    - Stage tracking
    - Immutable snapshots (for debugging / rollback)
    """

    # --------------------------------------------------
    # INIT
    # --------------------------------------------------
    def __init__(self, initial_input: Optional[Any] = None):
        super().__init__()

        self["input"] = initial_input
        self["design"] = {}
        self["logs"] = []
        self["errors"] = []
        self["context"] = []
        self["status"] = "INIT"
        self["stage"] = "start"
        self["history"] = []

    # --------------------------------------------------
    # LOGGING
    # --------------------------------------------------
    def log(self, message: str, level: str = "INFO"):
        entry = {
            "time": datetime.utcnow().isoformat(),
            "level": level,
            "message": message
        }
        self["logs"].append(entry)

    def get_logs(self) -> List[Dict[str, Any]]:
        return self["logs"]

    # --------------------------------------------------
    # ERROR HANDLING
    # --------------------------------------------------
    def add_error(self, error: str):
        entry = {
            "time": datetime.utcnow().isoformat(),
            "error": error
        }
        self["errors"].append(entry)
        self["status"] = "ERROR"

    def has_errors(self) -> bool:
        return len(self["errors"]) > 0

    def clear_errors(self):
        self["errors"] = []

    # --------------------------------------------------
    # DESIGN MANAGEMENT
    # --------------------------------------------------
    def update_design(self, design: Dict[str, Any]):
        self["design"] = design

    def get_design(self) -> Dict[str, Any]:
        return self.get("design", {})

    def merge_design(self, updates: Dict[str, Any]):
        """
        Merge partial updates into design
        """
        self["design"].update(updates)

    # --------------------------------------------------
    # CONTEXT (RAG / AGENTS)
    # --------------------------------------------------
    def set_context(self, context: List[Any]):
        self["context"] = context

    def add_context(self, item: Any):
        self["context"].append(item)

    def get_context(self) -> List[Any]:
        return self.get("context", [])

    # --------------------------------------------------
    # STAGE TRACKING
    # --------------------------------------------------
    def set_stage(self, stage: str):
        self["stage"] = stage
        self.log(f"Stage → {stage}")

    def get_stage(self) -> str:
        return self.get("stage", "")

    # --------------------------------------------------
    # STATUS CONTROL
    # --------------------------------------------------
    def set_status(self, status: str):
        self["status"] = status

    def get_status(self) -> str:
        return self.get("status", "")

    # --------------------------------------------------
    # SNAPSHOT / HISTORY
    # --------------------------------------------------
    def snapshot(self, label: str = ""):
        """
        Save state snapshot for debugging or rollback
        """
        snap = {
            "time": datetime.utcnow().isoformat(),
            "label": label,
            "design": copy.deepcopy(self["design"])
        }
        self["history"].append(snap)

    def get_history(self) -> List[Dict[str, Any]]:
        return self.get("history", [])

    # --------------------------------------------------
    # RESET
    # --------------------------------------------------
    def reset(self):
        self.clear()
        self.__init__()

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------
    def summary(self) -> Dict[str, Any]:
        design = self.get_design()

        return {
            "status": self.get_status(),
            "stage": self.get_stage(),
            "components": len(design.get("components", [])),
            "nets": len(design.get("nets", [])),
            "routes": len(design.get("routes", [])),
            "errors": len(self["errors"]),
            "logs": len(self["logs"])
        }

    # --------------------------------------------------
    # DEBUG PRINT
    # --------------------------------------------------
    def debug_print(self):
        print("\n===== PCB STATE =====")
        print("Status:", self.get_status())
        print("Stage:", self.get_stage())
        print("Errors:", len(self["errors"]))
        print("Logs:", len(self["logs"]))
        print("=====================\n")

    # --------------------------------------------------
    # SAFE GET
    # --------------------------------------------------
    def safe_get(self, key: str, default=None):
        return self.get(key, default)

    # --------------------------------------------------
    # STRING REPRESENTATION
    # --------------------------------------------------
    def __repr__(self):
        summary = self.summary()
        return f"<PCBState status={summary['status']} stage={summary['stage']} comps={summary['components']}>"
