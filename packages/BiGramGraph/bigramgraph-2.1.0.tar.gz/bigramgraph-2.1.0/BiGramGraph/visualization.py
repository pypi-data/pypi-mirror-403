"""Graph visualization utilities for BiGramGraph.

This module provides functions for visualizing BiGramGraph instances
using PyVis.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from pyvis.network import Network

if TYPE_CHECKING:
    from BiGramGraph.core import BiGramGraph


def visualize(
    graph: BiGramGraph,
    *,
    output_path: str | Path = "graph.html",
    height: int = 600,
    width: int = 1000,
    directed: bool = True,
    notebook: bool = False,
    physics_enabled: bool = True,
    show_weights: bool = False,
    node_color_by: str = "color",
) -> str:
    """Visualize a BiGramGraph as an interactive HTML network.

    Creates an interactive network visualization using PyVis and saves
    it to an HTML file.

    Args:
        graph: The BiGramGraph to visualize.
        output_path: Path to save the HTML file.
        height: Height of the visualization in pixels.
        width: Width of the visualization in pixels.
        directed: If True, show directed edges with arrows.
        notebook: If True, configure for Jupyter notebook rendering.
        physics_enabled: If True, enable physics simulation for layout.
        show_weights: If True, display edge weights as labels.
        node_color_by: Attribute to use for node coloring ('color' for
            chromatic color, 'pos' for part of speech if available).

    Returns:
        Path to the generated HTML file.

    Example:
        >>> from BiGramGraph import BiGramGraph
        >>> from BiGramGraph.visualization import visualize
        >>> graph = BiGramGraph(["the quick brown fox"])
        >>> visualize(graph, output_path="my_graph.html")
    """
    # Create network
    net = Network(
        height=f"{height}px",
        width=f"{width}px",
        notebook=notebook,
        directed=directed,
    )

    # Configure physics
    if physics_enabled:
        net.set_options("""
            var options = {
                "physics": {
                    "forceAtlas2Based": {
                        "gravitationalConstant": -100,
                        "springLength": 150,
                        "springConstant": 0.05,
                        "avoidOverlap": 0.5
                    },
                    "minVelocity": 0.75,
                    "solver": "forceAtlas2Based",
                    "timestep": 0.5
                }
            }
        """)
    else:
        net.toggle_physics(False)

    # Build color palette
    colors = _generate_color_palette(graph.chromatic_number)

    # Add nodes
    for _, row in graph.node_data.iterrows():
        word = row["word"]
        color_idx = row["color"]

        # Determine node color
        if node_color_by == "color":
            node_color = colors[color_idx % len(colors)]
        elif node_color_by == "pos" and "pos" in row:
            pos_colors = _get_pos_colors()
            node_color = pos_colors.get(row["pos"], "#cccccc")
        else:
            node_color = colors[color_idx % len(colors)]

        # Build title (tooltip)
        title = f"Word: {word}\nColor: {color_idx}"
        if "pos" in graph.node_data.columns:
            title += f"\nPOS: {row.get('pos', 'N/A')}"
        if "entity" in graph.node_data.columns and row.get("entity"):
            title += f"\nEntity: {row.get('entity')}"

        net.add_node(word, label=word, color=node_color, title=title)

    # Add edges
    for _, row in graph.edge_data.iterrows():
        source = row["source"]
        target = row["target"]
        weight = row["weight"]

        edge_kwargs: dict[str, Any] = {
            "value": weight,  # Affects edge thickness
        }
        if show_weights:
            edge_kwargs["label"] = str(weight)

        net.add_edge(source, target, **edge_kwargs)

    # Save and return path
    output_path = Path(output_path)
    if notebook:
        net.prep_notebook()

    net.save_graph(str(output_path))
    return str(output_path)


def visualize_subgraph(
    graph: BiGramGraph,
    nodes: list[str],
    *,
    output_path: str | Path = "subgraph.html",
    **kwargs: Any,
) -> str:
    """Visualize a subgraph containing only specified nodes.

    Args:
        graph: The BiGramGraph to visualize.
        nodes: List of node names to include in the visualization.
        output_path: Path to save the HTML file.
        **kwargs: Additional arguments passed to visualize().

    Returns:
        Path to the generated HTML file.
    """
    # Create a filtered view
    subgraph = graph.graph.subgraph(nodes)
    temp_graph = graph._from_subgraph(subgraph.copy())

    return visualize(temp_graph, output_path=output_path, **kwargs)


def _generate_color_palette(n: int) -> list[str]:
    """Generate a color palette with n distinct colors.

    Uses a combination of HSL color space to generate visually
    distinct colors.

    Args:
        n: Number of colors needed.

    Returns:
        List of hex color strings.
    """
    if n <= 0:
        return ["#cccccc"]

    # Predefined pleasing colors for small n
    base_colors = [
        "#e41a1c",  # red
        "#377eb8",  # blue
        "#4daf4a",  # green
        "#984ea3",  # purple
        "#ff7f00",  # orange
        "#ffff33",  # yellow
        "#a65628",  # brown
        "#f781bf",  # pink
        "#999999",  # gray
        "#66c2a5",  # teal
        "#fc8d62",  # salmon
        "#8da0cb",  # periwinkle
    ]

    if n <= len(base_colors):
        return base_colors[:n]

    # Generate additional colors using HSL
    colors = list(base_colors)
    for i in range(len(base_colors), n):
        hue = (i * 137.508) % 360  # Golden angle approximation
        colors.append(f"hsl({hue}, 70%, 50%)")

    return colors


def _get_pos_colors() -> dict[str, str]:
    """Get color mapping for part-of-speech tags.

    Returns:
        Dictionary mapping POS tags to colors.
    """
    return {
        "NOUN": "#e41a1c",
        "VERB": "#377eb8",
        "ADJ": "#4daf4a",
        "ADV": "#984ea3",
        "PROPN": "#ff7f00",
        "DET": "#ffff33",
        "PRON": "#a65628",
        "ADP": "#f781bf",
        "CONJ": "#999999",
        "CCONJ": "#999999",
        "SCONJ": "#999999",
        "NUM": "#66c2a5",
        "PUNCT": "#cccccc",
        "SYM": "#cccccc",
        "X": "#cccccc",
        "INTJ": "#fc8d62",
        "PART": "#8da0cb",
        "AUX": "#377eb8",
    }
