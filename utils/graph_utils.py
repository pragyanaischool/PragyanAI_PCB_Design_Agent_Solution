# utils/graph_utils.py

import networkx as nx


def netlist_to_graph(design: dict) -> nx.Graph:
    """
    Convert PCB netlist to graph
    Nodes: pins
    Edges: connections
    """
    G = nx.Graph()

    for net in design.get("nets", []):
        connections = net.get("connections", [])

        for conn in connections:
            G.add_node(conn)

        # Fully connect nodes within a net
        for i in range(len(connections)):
            for j in range(i + 1, len(connections)):
                G.add_edge(connections[i], connections[j], net=net["name"])

    return G


def get_connected_components(G: nx.Graph):
    return list(nx.connected_components(G))


def shortest_path(G: nx.Graph, source: str, target: str):
    try:
        return nx.shortest_path(G, source, target)
    except nx.NetworkXNoPath:
        return None


def graph_stats(G: nx.Graph) -> dict:
    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "components": nx.number_connected_components(G)
    }
  
