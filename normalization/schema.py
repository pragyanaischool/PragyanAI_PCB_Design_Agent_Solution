# normalization/schema.py

from typing import List, Optional, Dict, Tuple, Any
from pydantic import BaseModel, Field, validator


# --------------------------------------------------
# BASIC TYPES
# --------------------------------------------------
Coordinate = Tuple[float, float]


# --------------------------------------------------
# PIN
# --------------------------------------------------
class Pin(BaseModel):
    name: str = Field(..., description="Pin name (e.g., VCC, GND, 1)")
    number: Optional[str] = Field("", description="Pin number if available")


# --------------------------------------------------
# COMPONENT
# --------------------------------------------------
class Component(BaseModel):
    ref: str = Field(..., description="Reference designator (R1, U1)")
    value: Optional[str] = Field("", description="Component value")
    footprint: Optional[str] = Field("", description="Footprint name")
    pins: List[str] = Field(default_factory=list)

    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    # ----------------------------
    # VALIDATION
    # ----------------------------
    @validator("ref")
    def normalize_ref(cls, v):
        return v.strip().upper()

    @validator("pins", pre=True)
    def normalize_pins(cls, v):
        if isinstance(v, str):
            return [p.strip() for p in v.split(",") if p.strip()]
        return v or []


# --------------------------------------------------
# NET
# --------------------------------------------------
class Net(BaseModel):
    name: str = Field(..., description="Net name")
    connections: List[str] = Field(default_factory=list)

    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator("name")
    def normalize_name(cls, v):
        return v.strip().upper()

    @validator("connections", pre=True)
    def normalize_connections(cls, v):
        if isinstance(v, str):
            return [c.strip() for c in v.split(",") if c.strip()]
        return list(set(v or []))


# --------------------------------------------------
# ROUTE
# --------------------------------------------------
class Route(BaseModel):
    net: str = Field(..., description="Net name")
    path: List[Coordinate] = Field(default_factory=list)
    width: float = Field(0.2, description="Trace width")

    layer: Optional[str] = Field("top", description="PCB layer")

    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


# --------------------------------------------------
# LAYOUT (PLACEMENT)
# --------------------------------------------------
class Placement(BaseModel):
    x: float
    y: float
    rotation: Optional[float] = 0.0
    layer: Optional[str] = "top"


Layout = Dict[str, Placement]  # { "R1": Placement(...) }


# --------------------------------------------------
# DESIGN (MASTER OBJECT)
# --------------------------------------------------
class Design(BaseModel):
    components: List[Component]
    nets: List[Net]

    layout: Optional[Layout] = Field(default_factory=dict)
    routes: Optional[List[Route]] = Field(default_factory=list)

    constraints: Optional[Dict[str, Any]] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    # --------------------------------------------------
    # GLOBAL VALIDATION
    # --------------------------------------------------
    @validator("components")
    def check_unique_refs(cls, comps):
        refs = set()
        for c in comps:
            if c.ref in refs:
                raise ValueError(f"Duplicate component ref: {c.ref}")
            refs.add(c.ref)
        return comps

    @validator("nets")
    def check_valid_connections(cls, nets):
        for net in nets:
            for conn in net.connections:
                if ":" not in conn:
                    raise ValueError(f"Invalid connection format: {conn}")
        return nets

    # --------------------------------------------------
    # UTILITY METHODS
    # --------------------------------------------------
    def get_component(self, ref: str) -> Optional[Component]:
        for c in self.components:
            if c.ref == ref:
                return c
        return None

    def get_net(self, name: str) -> Optional[Net]:
        for n in self.nets:
            if n.name == name:
                return n
        return None

    def to_dict(self) -> Dict[str, Any]:
        return self.dict()

    def summary(self) -> Dict[str, int]:
        return {
            "components": len(self.components),
            "nets": len(self.nets),
            "routes": len(self.routes),
            "placed": len(self.layout)
        }


# --------------------------------------------------
# FACTORY FUNCTION
# --------------------------------------------------
def create_design(data: Dict[str, Any]) -> Design:
    """
    Safe creation of Design object
    """
    return Design(**data)


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample = {
        "components": [
            {"ref": "R1", "value": "10k", "pins": ["1", "2"]},
            {"ref": "C1", "value": "100nF", "pins": "1,2"}
        ],
        "nets": [
            {"name": "VCC", "connections": ["R1:1", "C1:1"]},
            {"name": "GND", "connections": "R1:2,C1:2"}
        ],
        "layout": {
            "R1": {"x": 10, "y": 20},
            "C1": {"x": 30, "y": 40}
        }
    }

    design = create_design(sample)

    print("\nDesign Summary:", design.summary())
    print("\nSerialized:", design.to_dict())
  
