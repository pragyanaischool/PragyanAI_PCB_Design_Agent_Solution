# enrichment/hierarchy.py

from typing import Dict, Any, List
from copy import deepcopy

from utils.logger import get_module_logger

logger = get_module_logger(__name__)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def build_path(parent_path: str, ref: str) -> str:
    return f"{parent_path}/{ref}" if parent_path else ref


def prefix_ref(ref: str, path: str) -> str:
    """
    Convert R1 → TOP/U1/R1 → TOP_U1_R1
    """
    return path.replace("/", "_")


def remap_connection(conn: str, ref_map: Dict[str, str]) -> str:
    """
    Remap connection like R1:1 → TOP_U1_R1:1
    """
    try:
        ref, pin = conn.split(":")
        new_ref = ref_map.get(ref, ref)
        return f"{new_ref}:{pin}"
    except:
        return conn


# --------------------------------------------------
# MAIN FLATTEN FUNCTION
# --------------------------------------------------
def flatten_hierarchy(design: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten hierarchical design into single-level design
    """

    logger.info("Flattening hierarchy")

    flat_components = []
    flat_nets = []

    ref_map = {}  # old ref → new ref

    # --------------------------------------------------
    # PROCESS COMPONENTS
    # --------------------------------------------------
    def process_components(components, parent_path=""):
        for comp in components:
            ref = comp.get("ref")

            if not ref:
                continue

            path = build_path(parent_path, ref)
            new_ref = prefix_ref(ref, path)

            ref_map[ref] = new_ref

            new_comp = deepcopy(comp)
            new_comp["ref"] = new_ref
            new_comp["hier_path"] = path

            # Remove children after flatten
            children = new_comp.pop("children", None)

            flat_components.append(new_comp)

            # Recursively process children
            if children:
                process_components(children, path)

    process_components(design.get("components", []))

    # --------------------------------------------------
    # PROCESS NETS
    # --------------------------------------------------
    def process_nets(nets):
        for net in nets:
            new_net = deepcopy(net)

            new_connections = []

            for conn in net.get("connections", []):
                new_connections.append(remap_connection(conn, ref_map))

            new_net["connections"] = list(set(new_connections))

            flat_nets.append(new_net)

    process_nets(design.get("nets", []))

    # --------------------------------------------------
    # FINAL DESIGN
    # --------------------------------------------------
    flat_design = {
        "components": flat_components,
        "nets": flat_nets,
        "metadata": {
            "flattened": True,
            "original_hierarchy": True
        }
    }

    logger.info(
        f"Hierarchy flattened → {len(flat_components)} components"
    )

    return flat_design


# --------------------------------------------------
# BUILD HIERARCHY TREE (OPTIONAL)
# --------------------------------------------------
def build_hierarchy_tree(design: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert flat design back into hierarchy tree (best-effort)
    """

    tree = {}

    for comp in design.get("components", []):
        path = comp.get("hier_path", "")
        parts = path.split("/")

        node = tree

        for p in parts[:-1]:
            node = node.setdefault(p, {})

        node[parts[-1]] = comp

    return tree


# --------------------------------------------------
# VALIDATE HIERARCHY
# --------------------------------------------------
def validate_hierarchy(design: Dict[str, Any]) -> List[str]:
    """
    Check hierarchy integrity
    """

    errors = []

    refs = set()

    for comp in design.get("components", []):
        ref = comp.get("ref")

        if ref in refs:
            errors.append(f"Duplicate ref in hierarchy: {ref}")

        refs.add(ref)

    return errors


# --------------------------------------------------
# NET PROPAGATION (ADVANCED)
# --------------------------------------------------
def propagate_nets(design: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure nets propagate across hierarchical boundaries
    """

    logger.info("Propagating nets")

    nets = design.get("nets", [])

    net_map = {}

    for net in nets:
        name = net["name"]

        if name not in net_map:
            net_map[name] = set()

        for conn in net.get("connections", []):
            net_map[name].add(conn)

    # Merge nets
    merged_nets = [
        {
            "name": name,
            "connections": list(conns)
        }
        for name, conns in net_map.items()
    ]

    design["nets"] = merged_nets

    return design


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample = {
        "components": [
            {
                "ref": "U1",
                "children": [
                    {"ref": "R1"},
                    {"ref": "C1"}
                ]
            },
            {"ref": "R2"}
        ],
        "nets": [
            {"name": "SIG", "connections": ["R1:1", "R2:1"]}
        ]
    }

    flat = flatten_hierarchy(sample)

    from pprint import pprint
    pprint(flat)
  
