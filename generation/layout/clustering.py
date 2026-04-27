# generation/layout/clustering.py

from typing import Dict, Any, List, Set
import networkx as nx
import math

from utils.logger import get_module_logger
from utils.graph_utils import netlist_to_graph
from config.settings import settings


logger = get_module_logger(__name__)

GRID_SIZE = settings.GRID_SIZE


# --------------------------------------------------
# EXTRACT COMPONENT FROM PIN NODE
# --------------------------------------------------
def get_ref(node: str) -> str:
    """
    Extract component ref from node like 'U1:VCC'
    """
    try:
        return node.split(":")[0]
    except Exception:
        return node


# --------------------------------------------------
# BUILD COMPONENT GRAPH (REF-LEVEL GRAPH)
# --------------------------------------------------
def build_component_graph(design: Dict[str, Any]) -> nx.Graph:
    """
    Convert pin-level graph → component-level graph
    """
    pin_graph = netlist_to_graph(design)

    comp_graph = nx.Graph()

    for u, v, data in pin_graph.edges(data=True):
        r1 = get_ref(u)
        r2 = get_ref(v)

        if r1 == r2:
            continue

        if comp_graph.has_edge(r1, r2):
            comp_graph[r1][r2]["weight"] += 1
        else:
            comp_graph.add_edge(r1, r2, weight=1)

    logger.debug(f"Component graph nodes: {comp_graph.number_of_nodes()}")
    logger.debug(f"Component graph edges: {comp_graph.number_of_edges()}")

    return comp_graph


# --------------------------------------------------
# FIND CONNECTED CLUSTERS
# --------------------------------------------------
def find_clusters(comp_graph: nx.Graph) -> List[Set[str]]:
    """
    Each connected component = cluster
    """
    clusters = list(nx.connected_components(comp_graph))

    logger.info(f"Found {len(clusters)} clusters")

    return clusters


# --------------------------------------------------
# SORT CLUSTERS BY SIZE (IMPORTANT FOR PLACEMENT)
# --------------------------------------------------
def sort_clusters(clusters: List[Set[str]]) -> List[Set[str]]:
    return sorted(clusters, key=lambda c: len(c), reverse=True)


# --------------------------------------------------
# COMPUTE CLUSTER CENTERS (GRID DISTRIBUTION)
# --------------------------------------------------
def compute_cluster_centers(num_clusters: int):
    """
    Spread clusters across board
    """
    centers = []

    cols = max(1, int(math.sqrt(num_clusters)))
    rows = math.ceil(num_clusters / cols)

    spacing_x = settings.BOARD_WIDTH // (cols + 1)
    spacing_y = settings.BOARD_HEIGHT // (rows + 1)

    for i in range(num_clusters):
        row = i // cols
        col = i % cols

        cx = (col + 1) * spacing_x
        cy = (row + 1) * spacing_y

        centers.append((cx, cy))

    return centers


# --------------------------------------------------
# PLACE COMPONENTS WITHIN CLUSTER
# --------------------------------------------------
def place_cluster(cluster: Set[str], center_x: int, center_y: int):
    """
    Place cluster components in small grid around center
    """
    layout = {}

    size = len(cluster)
    grid_dim = max(1, int(math.sqrt(size)))

    i = 0
    for ref in cluster:
        row = i // grid_dim
        col = i % grid_dim

        x = center_x + col * GRID_SIZE
        y = center_y + row * GRID_SIZE

        layout[ref] = {"x": x, "y": y}

        i += 1

    return layout


# --------------------------------------------------
# MAIN CLUSTERING PLACEMENT
# --------------------------------------------------
def cluster_placement(design: Dict[str, Any]) -> Dict[str, Dict]:
    """
    Returns layout dict:
    {
        "R1": {"x": 10, "y": 20},
        ...
    }
    """

    logger.info("Starting clustering-based placement")

    comp_graph = build_component_graph(design)

    if comp_graph.number_of_nodes() == 0:
        logger.warning("Empty graph → fallback to simple placement")
        return {}

    clusters = find_clusters(comp_graph)
    clusters = sort_clusters(clusters)

    centers = compute_cluster_centers(len(clusters))

    final_layout = {}

    for idx, cluster in enumerate(clusters):
        cx, cy = centers[idx]

        cluster_layout = place_cluster(cluster, cx, cy)

        final_layout.update(cluster_layout)

    logger.info(f"Cluster placement complete: {len(final_layout)} components")

    return final_layout


# --------------------------------------------------
# ADVANCED: WEIGHTED CLUSTERING (OPTIONAL)
# --------------------------------------------------
def weighted_cluster_priority(comp_graph: nx.Graph):
    """
    Prioritize highly connected components (hubs)
    """
    centrality = nx.degree_centrality(comp_graph)

    sorted_nodes = sorted(
        centrality.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return [node for node, _ in sorted_nodes]


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample_design = {
        "components": [
            {"ref": "U1"},
            {"ref": "U2"},
            {"ref": "R1"},
            {"ref": "C1"},
            {"ref": "R2"},
        ],
        "nets": [
            {"name": "VCC", "connections": ["U1:1", "R1:1", "C1:1"]},
            {"name": "SIG", "connections": ["U1:2", "U2:1"]},
            {"name": "GND", "connections": ["U2:2", "R2:1"]},
        ]
    }

    layout = cluster_placement(sample_design)

    for k, v in layout.items():
        print(k, v)
      
