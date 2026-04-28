# scripts/generate_samples.py

import json
from pathlib import Path
import random

from utils.logger import get_module_logger

logger = get_module_logger(__name__)


# --------------------------------------------------
# SAMPLE GENERATORS
# --------------------------------------------------
def resistor_divider():
    return {
        "components": [
            {"ref": "R1", "value": "10k"},
            {"ref": "R2", "value": "10k"},
        ],
        "nets": [
            {"name": "VCC", "connections": ["R1:1"]},
            {"name": "MID", "connections": ["R1:2", "R2:1"]},
            {"name": "GND", "connections": ["R2:2"]},
        ]
    }


def rc_filter():
    return {
        "components": [
            {"ref": "R1", "value": "1k"},
            {"ref": "C1", "value": "100nF"},
        ],
        "nets": [
            {"name": "IN", "connections": ["R1:1"]},
            {"name": "OUT", "connections": ["R1:2", "C1:1"]},
            {"name": "GND", "connections": ["C1:2"]},
        ]
    }


def microcontroller_basic():
    return {
        "components": [
            {"ref": "U1", "value": "ATmega328"},
            {"ref": "C1", "value": "100nF"},
        ],
        "nets": [
            {"name": "VCC", "connections": ["U1:VCC", "C1:1"]},
            {"name": "GND", "connections": ["U1:GND", "C1:2"]},
        ]
    }


def random_design(n=5):
    comps = []
    nets = []

    for i in range(n):
        comps.append({
            "ref": f"R{i+1}",
            "value": f"{random.randint(1,100)}k"
        })

    nets.append({
        "name": "NET1",
        "connections": [f"R{i+1}:1" for i in range(n)]
    })

    return {
        "components": comps,
        "nets": nets
    }


# --------------------------------------------------
# SAVE
# --------------------------------------------------
def save_samples(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    samples = [
        resistor_divider(),
        rc_filter(),
        microcontroller_basic(),
        random_design(5),
        random_design(8),
    ]

    for i, sample in enumerate(samples):
        path = output_dir / f"sample_{i+1}.json"

        with open(path, "w") as f:
            json.dump(sample, f, indent=2)

        logger.info(f"Saved {path}")


# --------------------------------------------------
# RUN
# --------------------------------------------------
if __name__ == "__main__":
    save_samples(Path("data/samples"))
