"""Graph analysis functions for BiGramGraph.

This module contains utility functions for analyzing paths, cycles,
and computing graph metrics.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from BiGramGraph.exceptions import MissingEnrichmentError

if TYPE_CHECKING:
    from BiGramGraph.core import BiGramGraph


def calculate_path_weight(
    graph: BiGramGraph,
    path: list[str],
) -> float:
    """Calculate the total weight along a path in the graph.

    The weight is the sum of edge weights between consecutive nodes.

    Args:
        graph: The BiGramGraph instance.
        path: List of node names representing the path.

    Returns:
        Sum of edge weights along the path.

    Example:
        >>> path = ["the", "quick", "brown"]
        >>> weight = calculate_path_weight(graph, path)
    """
    if len(path) < 2:
        return 0.0

    weight = 0.0
    for i in range(len(path) - 1):
        source, target = path[i], path[i + 1]
        mask = (graph.edge_data["source"] == source) & (graph.edge_data["target"] == target)
        matches = graph.edge_data[mask]
        if not matches.empty:
            weight += matches["weight"].values[0]

    return weight


def calculate_path_density(
    graph: BiGramGraph,
    path: list[str],
) -> float:
    """Calculate the density of a path based on node degrees.

    The density is computed as the sum of square roots of total degrees
    for each node in the path.

    Args:
        graph: The BiGramGraph instance.
        path: List of node names representing the path.

    Returns:
        The path density value.
    """
    density = 0.0
    for node in path:
        if node in graph.graph.nodes:
            in_deg = graph.graph.in_degree(node)
            out_deg = graph.graph.out_degree(node)
            density += np.sqrt(in_deg + out_deg)

    return density


def calculate_cycle_density(
    graph: BiGramGraph,
    cycle: list[tuple[str, str]],
) -> float:
    """Calculate the density of a cycle based on node degrees.

    Args:
        graph: The BiGramGraph instance.
        cycle: List of edge tuples representing the cycle.

    Returns:
        Sum of square roots of total degrees for nodes in the cycle.
    """
    density = 0.0
    for edge in cycle:
        node = edge[0]
        if node in graph.graph.nodes:
            in_deg = graph.graph.in_degree(node)
            out_deg = graph.graph.out_degree(node)
            density += np.sqrt(in_deg + out_deg)

    return density


def chromatic_distance(
    graph1: BiGramGraph,
    graph2: BiGramGraph,
) -> float:
    """Calculate the chromatic distance (psi similarity) between two graphs.

    This implements the psi similarity coefficient as presented in the paper
    "On Bi Gram Graph attributes". The metric measures how similar two graphs
    are based on their chromatic coloring of overlapping words.

    Args:
        graph1: First BiGramGraph to compare.
        graph2: Second BiGramGraph to compare.

    Returns:
        The psi similarity coefficient (IC / I), where:
        - I is the number of overlapping words
        - IC is the number of overlapping words with the same chromatic color

    Raises:
        MissingEnrichmentError: If POS tags haven't been computed for both graphs.

    Example:
        >>> graph1 = BiGramGraph(texts1)
        >>> graph2 = BiGramGraph(texts2)
        >>> graph1.enrich_pos()
        >>> graph2.enrich_pos()
        >>> similarity = chromatic_distance(graph1, graph2)
    """
    if "pos" not in graph1.node_data.columns:
        raise MissingEnrichmentError(
            "POS tags required for graph1. Call graph1.enrich_pos() first."
        )
    if "pos" not in graph2.node_data.columns:
        raise MissingEnrichmentError(
            "POS tags required for graph2. Call graph2.enrich_pos() first."
        )

    # Find overlapping words
    words1 = set(graph1.node_data["word"])
    words2 = set(graph2.node_data["word"])
    overlapping = words1 & words2

    if not overlapping:
        return 0.0

    num_overlapping = len(overlapping)

    # Create comparison dataframe
    overlap_list = list(overlapping)
    colors1 = graph1.node_data.set_index("word").loc[overlap_list, "color"]
    colors2 = graph2.node_data.set_index("word").loc[overlap_list, "color"]

    # Count words with same chromatic number
    same_color = (colors1 == colors2).sum()

    return same_color / num_overlapping


def graph_similarity_report(
    graph1: BiGramGraph,
    graph2: BiGramGraph,
) -> dict[str, float | int]:
    """Generate a comprehensive similarity report between two graphs.

    Args:
        graph1: First BiGramGraph to compare.
        graph2: Second BiGramGraph to compare.

    Returns:
        Dictionary containing various similarity metrics:
        - overlapping_words: Number of words in both graphs
        - jaccard_words: Jaccard similarity of word sets
        - chromatic_distance: Chromatic distance (if POS available)
        - size_ratio: Ratio of graph sizes (smaller/larger)
    """
    words1 = set(graph1.node_data["word"])
    words2 = set(graph2.node_data["word"])

    overlap = words1 & words2
    union = words1 | words2

    report = {
        "overlapping_words": len(overlap),
        "total_unique_words": len(union),
        "jaccard_similarity": len(overlap) / len(union) if union else 0.0,
        "size_ratio": min(graph1.num_nodes, graph2.num_nodes) / max(graph1.num_nodes, graph2.num_nodes),
    }

    # Add chromatic distance if POS tags are available
    if "pos" in graph1.node_data.columns and "pos" in graph2.node_data.columns:
        report["chromatic_distance"] = chromatic_distance(graph1, graph2)

    return report
