# app/components/pcb_viewer.py

import streamlit as st
import matplotlib.pyplot as plt


# --------------------------------------------------
# MAIN VIEWER
# --------------------------------------------------
def show_pcb(design):
    """
    Main entry to visualize PCB
    """

    if not design:
        st.warning("No design to display")
        return

    st.subheader("📊 PCB Layout Viewer")

    layout = design.get("layout", {})
    routes = design.get("routes", [])
    components = design.get("components", [])

    if not layout:
        st.warning("⚠️ No layout found. Run placement first.")
        _show_component_list(components)
        return

    # Plot
    fig, ax = plt.subplots(figsize=(8, 6))

    # Draw components
    for comp in components:
        ref = comp.get("ref")

        if ref in layout:
            x = layout[ref]["x"]
            y = layout[ref]["y"]

            ax.scatter(x, y)
            ax.text(x + 0.5, y + 0.5, ref, fontsize=8)

    # Draw routes
    for route in routes:
        path = route.get("path", [])

        if len(path) >= 2:
            xs = [p[0] for p in path]
            ys = [p[1] for p in path]

            ax.plot(xs, ys, linewidth=2)

    ax.set_title("PCB Layout")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.grid(True)

    st.pyplot(fig)

    # Additional Info
    _show_summary(design)


# --------------------------------------------------
# SUMMARY PANEL
# --------------------------------------------------
def _show_summary(design):
    st.subheader("📋 Design Summary")

    col1, col2, col3 = st.columns(3)

    col1.metric("Components", len(design.get("components", [])))
    col2.metric("Nets", len(design.get("nets", [])))
    col3.metric("Routes", len(design.get("routes", [])))


# --------------------------------------------------
# COMPONENT LIST (Fallback)
# --------------------------------------------------
def _show_component_list(components):
    st.subheader("🔧 Components")

    for comp in components:
        st.write(f"{comp.get('ref')} - {comp.get('value', '')}")


# --------------------------------------------------
# NET HIGHLIGHT VIEW
# --------------------------------------------------
def show_net(design, net_name):
    """
    Highlight specific net
    """

    layout = design.get("layout", {})
    nets = design.get("nets", [])

    fig, ax = plt.subplots(figsize=(8, 6))

    # Plot all components
    for ref, pos in layout.items():
        ax.scatter(pos["x"], pos["y"], color="gray")

    # Highlight selected net
    for net in nets:
        if net["name"] == net_name:
            for conn in net["connections"]:
                ref = conn.split(":")[0]

                if ref in layout:
                    pos = layout[ref]
                    ax.scatter(pos["x"], pos["y"], color="red", s=80)
                    ax.text(pos["x"], pos["y"], ref)

    ax.set_title(f"Net Highlight: {net_name}")
    st.pyplot(fig)


# --------------------------------------------------
# INTERACTIVE SELECTOR
# --------------------------------------------------
def interactive_view(design):
    """
    Interactive UI controls
    """

    st.subheader("🎛 Interactive PCB Viewer")

    nets = [n["name"] for n in design.get("nets", [])]

    selected_net = st.selectbox("Select Net", ["All"] + nets)

    if selected_net == "All":
        show_pcb(design)
    else:
        show_net(design, selected_net)


# --------------------------------------------------
# DEBUG
# --------------------------------------------------
if __name__ == "__main__":
    sample = {
        "components": [
            {"ref": "R1"},
            {"ref": "R2"}
        ],
        "layout": {
            "R1": {"x": 0, "y": 0},
            "R2": {"x": 10, "y": 10}
        },
        "routes": [
            {"path": [(0, 0), (10, 10)]}
        ],
        "nets": [
            {"name": "SIG", "connections": ["R1:1", "R2:1"]}
        ]
    }

    # This won't run standalone (needs Streamlit)
    print("Run inside Streamlit app")
  
