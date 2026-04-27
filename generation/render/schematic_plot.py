# generation/render/schematic_plot.py

from typing import Dict, Any, Tuple
import matplotlib.pyplot as plt
import networkx as nx

from utils.logger import get_module_logger
from utils.output_manager import OutputManager

logger = get_module_logger(__name__)
output_manager = OutputManager()


# --------------------------------------------------
# BUILD COMPONENT-LEVEL GRAPH
# --------------------------------------------------
def build_component_graph(design: Dict[str, Any]) -> nx.Graph:
    """
    Convert netlist into component-level graph
    Nodes: components
    Edges: connections via nets
    """

    G = nx.Graph()

    components = design.get("components", [])
    nets = design.get("nets", [])

    # Add nodes
    for comp in components:
        ref = comp.get("ref")
        value = comp.get("value", "")
        G.add_node(ref, label=f"{ref}\n{value}")

    # Add edges
    for net in nets:
        connections = net.get("connections", [])
        refs = [c.split(":")[0] for c in connections]

        for i in range(len(refs)):
            for j in range(i + 1, len(refs)):
                r1, r2 = refs[i], refs[j]

                if G.has_edge(r1, r2):
                    G[r1][r2]["nets"].append(net["name"])
                else:
                    G.add_edge(r1, r2, nets=[net["name"]])

    return G


# --------------------------------------------------
# LAYOUT ENGINE
# --------------------------------------------------
def compute_layout(G: nx.Graph):
    """
    Try multiple layouts for better visualization
    """

    if len(G.nodes) <= 10:
        return nx.spring_layout(G, seed=42)

    try:
        return nx.kamada_kawai_layout(G)
    except Exception:
        return nx.spring_layout(G)


# --------------------------------------------------
# DRAW GRAPH
# --------------------------------------------------
def draw_graph(G: nx.Graph, pos: Dict[str, Tuple[float, float]], ax):
    """
    Draw nodes + edges with labels
    """

    # Nodes
    labels = nx.get_node_attributes(G, "label")

    nx.draw_networkx_nodes(
        G, pos,
        node_size=800,
        node_color="lightblue",
        ax=ax
    )

    nx.draw_networkx_labels(
        G, pos,
        labels=labels,
        font_size=8,
        ax=ax
    )

    # Edges
    nx.draw_networkx_edges(G, pos, ax=ax)

    # Edge labels (net names)
    edge_labels = {
        (u, v): ",".join(data.get("nets", []))
        for u, v, data in G.edges(data=True)
    }

    nx.draw_networkx_edge_labels(
        G, pos,
        edge_labels=edge_labels,
        font_size=6,
        ax=ax
    )


# --------------------------------------------------
# MAIN FUNCTION
# --------------------------------------------------
def draw_schematic(design: Dict[str, Any]):
    """
    Render schematic as component-level graph
    """

    logger.info("Rendering schematic")

    try:
        G = build_component_graph(design)

        if G.number_of_nodes() == 0:
            logger.warning("No components to render")
            return None

        pos = compute_layout(G)

        fig, ax = plt.subplots(figsize=(10, 8))

        draw_graph(G, pos, ax)

        ax.set_title("Schematic Diagram")
        ax.axis("off")

        # Save output
        path = output_manager.save_image(fig, "schematic")

        plt.close(fig)

        logger.info(f"Schematic saved: {path}")

        return path

    except Exception as e:
        logger.error(f"Schematic rendering failed: {e}")
        return None


# --------------------------------------------------
# OPTIONAL: HIERARCHICAL VIEW (GROUP BY NET)
# --------------------------------------------------
def draw_net_grouped_schematic(design: Dict[str, Any]):
    """
    Alternative view: group by nets
    """

    G = nx.Graph()

    nets = design.get("nets", [])

    for net in nets:
        net_name = net.get("name")

        for conn in net.get("connections", []):
            ref = conn.split(":")[0]
            G.add_node(ref)

        refs = [c.split(":")[0] for c in net.get("connections", [])]

        for i in range(len(refs)):
            for j in range(i + 1, len(refs)):
                G.add_edge(refs[i], refs[j], label=net_name)

    pos = nx.spring_layout(G)

    fig, ax = plt.subplots(figsize=(10, 8))

    nx.draw(G, pos, with_labels=True, node_size=700, ax=ax)

    edge_labels = nx.get_edge_attributes(G, "label")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax)

    ax.set_title("Net Grouped Schematic")

    path = output_manager.save_image(fig, "schematic_net")

    plt.close(fig)

    return path


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    sample_design = {
        "components": [
            {"ref": "U1", "value": "ATmega"},
            {"ref": "R1", "value": "10k"},
            {"ref": "C1", "value": "100nF"},
        ],
        "nets": [
            {"name": "VCC", "connections": ["U1:VCC", "R1:1"]},
            {"name": "GND", "connections": ["U1:GND", "C1:2"]},
            {"name": "SIG", "connections": ["U1:PB0", "R1:2", "C1:1"]},
        ]
    }

    draw_schematic(sample_design)
    draw_net_grouped_schematic(sample_design)
