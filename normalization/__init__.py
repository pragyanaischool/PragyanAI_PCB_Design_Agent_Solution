# normalization/__init__.py

from .normalize import normalize_design
from .validator import validate_design
from .schema import Design

__all__ = [
    "normalize_design",
    "validate_design",
    "Design"
]
