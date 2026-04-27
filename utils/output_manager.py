# utils/output_manager.py

from pathlib import Path
from datetime import datetime
import uuid
from config.settings import settings
from utils.file_utils import ensure_dir
from utils.json_utils import write_json


class OutputManager:
    def __init__(self):
        self.base_dir = settings.OUTPUT_DIR

        self.dirs = {
            "images": settings.IMAGE_DIR,
            "schematics": settings.SCHEMATIC_DIR,
            "pcbs": settings.PCB_DIR,
            "gerbers": settings.OUTPUT_DIR / "gerbers",
            "netlists": settings.NETLIST_DIR,
            "logs": settings.LOG_DIR,
        }

        self._ensure_all_dirs()

    # --------------------------------------------------
    # INIT DIRS
    # --------------------------------------------------
    def _ensure_all_dirs(self):
        for path in self.dirs.values():
            ensure_dir(path)

    # --------------------------------------------------
    # UNIQUE FILE NAME
    # --------------------------------------------------
    def generate_filename(self, prefix: str, ext: str):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        uid = str(uuid.uuid4())[:6]
        return f"{prefix}_{timestamp}_{uid}.{ext}"

    # --------------------------------------------------
    # SAVE IMAGE
    # --------------------------------------------------
    def save_image(self, fig, name="pcb"):
        filename = self.generate_filename(name, "png")
        path = self.dirs["images"] / filename

        fig.savefig(path)
        return path

    # --------------------------------------------------
    # SAVE SCHEMATIC
    # --------------------------------------------------
    def save_schematic(self, content: str, name="schematic"):
        filename = self.generate_filename(name, "svg")
        path = self.dirs["schematics"] / filename

        with open(path, "w") as f:
            f.write(content)

        return path

    # --------------------------------------------------
    # SAVE NETLIST
    # --------------------------------------------------
    def save_netlist(self, data: dict, name="netlist"):
        filename = self.generate_filename(name, "json")
        path = self.dirs["netlists"] / filename

        write_json(data, path)
        return path

    # --------------------------------------------------
    # SAVE PCB DESIGN
    # --------------------------------------------------
    def save_pcb(self, design: dict, name="pcb"):
        filename = self.generate_filename(name, "json")
        path = self.dirs["pcbs"] / filename

        write_json(design, path)
        return path

    # --------------------------------------------------
    # SAVE GERBER (SIMULATED)
    # --------------------------------------------------
    def save_gerber(self, content: str, name="gerber"):
        filename = self.generate_filename(name, "gbr")
        path = self.dirs["gerbers"] / filename

        with open(path, "w") as f:
            f.write(content)

        return path

    # --------------------------------------------------
    # LIST FILES
    # --------------------------------------------------
    def list_outputs(self, category: str):
        if category not in self.dirs:
            raise ValueError("Invalid category")

        return list(self.dirs[category].glob("*"))

    # --------------------------------------------------
    # GET LATEST FILE
    # --------------------------------------------------
    def get_latest(self, category: str):
        files = self.list_outputs(category)
        if not files:
            return None

        return max(files, key=lambda f: f.stat().st_mtime)
      
