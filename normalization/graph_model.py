# normalization/graph_model.py

from typing import Dict, Any, List, Tuple
import networkx as nx

from utils.logger import get_module_logger

logger = get_module_logger(__name__)


# --------------------------------------------------
# DESIGN → COMPONENT GRAPH
# --------------------------------------------------
def design_to_component_graph(design: Dict[str, Any]) -> nx.Graph:
    """
    Nodes: components
    Edges: shared nets
    """

    G = nx.Graph()

    # Add component nodes
    for comp in design.get("components", []):
        G.add_node(
            comp["ref"],
            type="component",
            value=comp.get("value"),
            footprint=comp.get("footprint")
        )

    # Add edges based on nets
    for net in design.get("nets", []):
        refs = [c.split(":")[0] for c in net.get("connections", [])]

        for i in range(len(refs)):
            for j in range(i + 1, len(refs)):
                G.add_edge(
                    refs[i],
                    refs[j],
                    net=net["name"]
                )

    logger.info(f"Component graph: {G.number_of_nodes()} nodes")

    return G


# --------------------------------------------------
# DESIGN → BIPARTITE GRAPH
# --------------------------------------------------
def design_to_bipartite_graph(design: Dict[str, Any]) -> nx.Graph:
    """
    Nodes: components + nets
    Edges: component ↔ net
    """

    G = nx.Graph()

    # Components
    for comp in design.get("components", []):
        G.add_node(comp["ref"], type="component")

    # Nets
    for net in design.get("nets", []):
        net_name = net["name"]
        G.add_node(net_name, type="net")

        for conn in net.get("connections", []):
            ref = conn.split(":")[0]
            G.add_edge(ref, net_name)

    logger.info(f"Bipartite graph: {G.number_of_nodes()} nodes")

    return G


# --------------------------------------------------
# DESIGN → PIN-LEVEL GRAPH
# --------------------------------------------------
def design_to_pin_graph(design: Dict[str, Any]) -> nx.Graph:
    """
    Nodes: ref:pin
    Edges: same net
    """

    G = nx.Graph()

    for net in design.get("nets", []):
        conns = net.get("connections", [])

        for conn in conns:
            G.add_node(conn, net=net["name"])

        for i in range(len(conns)):
            for j in range(i + 1, len(conns)):
                G.add_edge(conns[i], conns[j], net=net["name"])

    logger.info(f"Pin graph: {G.number_of_nodes()} nodes")

    return G


# --------------------------------------------------
# GRAPH → DESIGN
# --------------------------------------------------
def graph_to_design(G: nx.Graph) -> Dict[str, Any]:
    """
    Convert graph → basic design (lossy)
    """

    components = []
    nets = []

    for node, data in G.nodes(data=True):
        if data.get("type") == "component":
            components.append({"ref": node})

    # Simple edge-based nets
    for i, (u, v, data) in enumerate(G.edges(data=True)):
        nets.append({
            "name": data.get("net", f"NET_{i+1}"),
            "connections": [f"{u}:1", f"{v}:1"]
        })

    return {
        "components": components,
        "nets": nets
    }


# --------------------------------------------------
# CONNECTIVITY QUERIES
# --------------------------------------------------
def get_neighbors(G: nx.Graph, node: str) -> List[str]:
    return list(G.neighbors(node)) if node in G else []


def find_path(G: nx.Graph, src: str, dst: str) -> List[str]:
    try:
        return nx.shortest_path(G, src, dst)
    except:
        return []


def connected_components(G: nx.Graph):
    return list(nx.connected_components(G))


# --------------------------------------------------
# GRAPH METRICS
# --------------------------------------------------
def compute_metrics(G: nx.Graph) -> Dict[str, Any]:
    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "density": nx.density(G),
        "avg_degree": sum(dict(G.degree()).values()) / max(G.number_of_nodes(), 1)
    }


def centrality_analysis(G: nx.Graph):
    return {
        "degree": nx.degree_centrality(G),
        "betweenness": nx.betweenness_centrality(G)
    }


# --------------------------------------------------
# SUBGRAPH EXTRACTION
# --------------------------------------------------
def extract_subgraph(G: nx.Graph, nodes: List[str]) -> nx.Graph:
    return G.subgraph(nodes).copy()


# --------------------------------------------------
# NET-BASED CLUSTERING
# --------------------------------------------------
def cluster_by_nets(design: Dict[str, Any]) -> Dict[str, List[str]]:
    clusters = {}

    for net in design.get("nets", []):
        refs = [c.split(":")[0] for c in net.get("connections", [])]
        clusters[net["name"]] = list(set(refs))

    return clusters


# --------------------------------------------------
# CRITICAL COMPONENTS
# --------------------------------------------------
def find_critical_components(G: nx.Graph, top_n=5):
    centrality = nx.degree_centrality(G)
    sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
    return sorted_nodes[:top_n]


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample = {
        "components": [
            {"ref": "U1", "value": "MCU"},
            {"ref": "R1", "value": "10k"},
            {"ref": "C1", "value": "100nF"},
        ],
        "nets": [
            {"name": "VCC", "connections": ["U1:VCC", "R1:1"]},
            {"name": "GND", "connections": ["U1:GND", "C1:2"]},
            {"name": "SIG", "connections": ["U1:PB0", "R1:2", "C1:1"]},
        ]
    }

    G = design_to_component_graph(sample)

    print("Neighbors of U1:", get_neighbors(G, "U1"))
    print("Path U1 → C1:", find_path(G, "U1", "C1"))
    print("Metrics:", compute_metrics(G))
    print("Critical:", find_critical_components(G))
