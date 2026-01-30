"""BiGramGraph - Graph-based bigram analysis for NLP.

A Python library for analyzing text corpora using graph theory. Transforms text
into directed graphs where nodes are words and edges represent bigram relationships.

Based on the paper "On Bi Gram Graph attributes" (https://arxiv.org/abs/2107.02128).

Example:
    >>> from BiGramGraph import BiGramGraph, Vectorizer, TextGenerator
    >>>
    >>> # Create a graph from text
    >>> texts = ["the quick brown fox jumps over the lazy dog"]
    >>> graph = BiGramGraph(texts)
    >>>
    >>> # Analyze the graph
    >>> print(graph.num_nodes)
    >>> print(graph.chromatic_number)
    >>>
    >>> # Vectorize text
    >>> vectorizer = Vectorizer(graph)
    >>> vec = vectorizer.transform("the quick")
    >>>
    >>> # Generate text
    >>> generator = TextGenerator(graph)
    >>> generated = generator.generate(num_colors=3)
"""

from BiGramGraph.core import BiGramGraph, DegreeStats
from BiGramGraph.analysis import (
    calculate_cycle_density,
    calculate_path_density,
    calculate_path_weight,
    chromatic_distance,
    graph_similarity_report,
)
from BiGramGraph.exceptions import (
    BiGramGraphError,
    GraphNotConnectedError,
    GraphNotEulerianError,
    MissingEnrichmentError,
    NoCycleFoundError,
    NodeNotFoundError,
    NoPathFoundError,
)
from BiGramGraph.generator import TextGenerator
from BiGramGraph.vectorizer import Vectorizer
from BiGramGraph.visualization import visualize, visualize_subgraph

__all__ = [
    # Core
    "BiGramGraph",
    "DegreeStats",
    # Analysis
    "calculate_path_weight",
    "calculate_path_density",
    "calculate_cycle_density",
    "chromatic_distance",
    "graph_similarity_report",
    # Vectorization
    "Vectorizer",
    # Generation
    "TextGenerator",
    # Visualization
    "visualize",
    "visualize_subgraph",
    # Exceptions
    "BiGramGraphError",
    "GraphNotEulerianError",
    "GraphNotConnectedError",
    "NodeNotFoundError",
    "NoCycleFoundError",
    "NoPathFoundError",
    "MissingEnrichmentError",
]

__version__ = "2.1.0"
