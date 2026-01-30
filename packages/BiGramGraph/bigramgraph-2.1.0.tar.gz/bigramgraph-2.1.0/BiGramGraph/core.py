"""Core BiGramGraph class for bigram graph analysis.

This module contains the main BiGramGraph class that transforms text corpora
into directed graph representations of bigrams.
"""

from __future__ import annotations

import pickle
from collections.abc import Generator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import networkx as nx
import nltk
import numpy as np
import pandas as pd
import spacy
from nltk import ngrams
from tqdm import tqdm

from BiGramGraph.exceptions import (
    GraphNotConnectedError,
    GraphNotEulerianError,
    NoCycleFoundError,
    NodeNotFoundError,
    NoPathFoundError,
)

if TYPE_CHECKING:
    from spacy.language import Language

# Lazy-loaded spaCy model
_nlp_model: Language | None = None


def _get_nlp_model() -> Language:
    """Lazily load the spaCy NLP model."""
    global _nlp_model
    if _nlp_model is None:
        _nlp_model = spacy.load("en_core_web_sm")
    return _nlp_model


@dataclass
class DegreeStats:
    """Statistics about node degrees in the graph."""

    in_min: int
    in_max: int
    out_min: int
    out_max: int


class BiGramGraph:
    """Transform a corpus into a directed graph representation of bigrams.

    This class converts a text corpus (given as a list of strings) into a
    directed graph where nodes represent unique words and edges represent
    bigram relationships between consecutive words.

    Attributes:
        graph: NetworkX DiGraph representing the bigram structure.
        num_nodes: Number of nodes (unique words) in the graph.
        num_edges: Number of edges (bigram pairs) in the graph.
        node_data: DataFrame containing words and their chromatic colors.
        edge_data: DataFrame containing edge information and weights.
        name: Identifier for the graph (usually the corpus name).
        degree_stats: Statistics about in/out degrees.

    Example:
        >>> texts = ["the quick brown fox", "the lazy dog"]
        >>> graph = BiGramGraph(texts)
        >>> print(graph.num_nodes)
        7
        >>> print(graph.chromatic_number)
        3
    """

    def __init__(
        self,
        texts: list[str],
        *,
        name: str = "BiGramGraph",
        show_progress: bool = True,
    ) -> None:
        """Initialize a BiGramGraph from text data.

        Args:
            texts: List of text strings to convert into a bigram graph.
            name: Name identifier for this graph.
            show_progress: If True, show progress bars during processing.
        """
        self.name = name
        self._nlp: Language | None = None
        self._build_graph(texts, show_progress)

    def _build_graph(self, texts: list[str], show_progress: bool) -> None:
        """Build the graph from text data."""
        # Merge text into a single body and calculate bigrams
        tokenized_text = " ".join(texts).split()
        bigram_list = list(ngrams(tokenized_text, n=2))

        # Derive edge weights and unique words as nodes
        freq_dist = nltk.FreqDist(bigram_list)
        edges = list(freq_dist.keys())
        nodes = np.unique(np.array(edges).flatten())

        # Initialize directed graph
        self.graph = nx.DiGraph()
        self.graph.add_nodes_from(nodes)

        # Add edges with weights
        edge_iter = tqdm(edges, desc="Building graph", disable=not show_progress)
        for x, y in edge_iter:
            self.graph.add_edge(x, y, weight=freq_dist[(x, y)])

        # Compute basic attributes
        self.num_nodes = len(nodes)
        self.num_edges = len(edges)

        # Compute degree statistics
        in_degrees = dict(self.graph.in_degree).values()
        out_degrees = dict(self.graph.out_degree).values()
        self.degree_stats = DegreeStats(
            in_min=min(in_degrees),
            in_max=max(in_degrees),
            out_min=min(out_degrees),
            out_max=max(out_degrees),
        )

        # Apply graph coloring
        coloring = nx.algorithms.coloring.greedy_color(self.graph)
        self.node_data = pd.DataFrame({
            "word": list(coloring.keys()),
            "color": list(coloring.values()),
        })

        # Create edges dataframe with weights
        self.edge_data = pd.DataFrame(edges, columns=["source", "target"])
        self.edge_data["weight"] = self.edge_data.apply(
            lambda row: freq_dist[(row["source"], row["target"])], axis=1
        )

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def chromatic_number(self) -> int:
        """The chromatic number (Xi) of the graph."""
        return len(self.node_data["color"].unique())

    @property
    def is_dag(self) -> bool:
        """Whether the graph is a directed acyclic graph."""
        return nx.algorithms.dag.is_directed_acyclic_graph(self.graph)

    @property
    def is_strongly_connected(self) -> bool:
        """Whether the graph is strongly connected."""
        return nx.algorithms.components.is_strongly_connected(self.graph)

    @property
    def num_strongly_connected_components(self) -> int:
        """Number of strongly connected components."""
        return nx.algorithms.components.number_strongly_connected_components(self.graph)

    @property
    def diameter(self) -> int:
        """The diameter of the graph (longest shortest path).

        Raises:
            GraphNotConnectedError: If the graph is not strongly connected.
        """
        if not self.is_strongly_connected:
            raise GraphNotConnectedError(
                "Diameter is only defined for strongly connected graphs"
            )
        return nx.algorithms.distance_measures.diameter(self.graph)

    @property
    def min_edge_cover(self) -> set[tuple[str, str]]:
        """The minimum edge cover of the graph."""
        return nx.algorithms.covering.min_edge_cover(self.graph)

    # -------------------------------------------------------------------------
    # Graph Analysis Methods
    # -------------------------------------------------------------------------

    def shortest_path(
        self,
        source: str,
        target: str,
        *,
        weighted: bool = False,
        method: Literal["dijkstra", "bellman-ford"] = "dijkstra",
    ) -> list[str]:
        """Find the shortest path between two nodes.

        Args:
            source: The starting node.
            target: The target node.
            weighted: If True, consider edge weights.
            method: Algorithm to use ('dijkstra' or 'bellman-ford').

        Returns:
            List of nodes forming the shortest path.

        Raises:
            NodeNotFoundError: If source or target is not in the graph.
            NoPathFoundError: If no path exists between the nodes.
        """
        self._validate_nodes(source, target)
        weight = "weight" if weighted else None
        try:
            return nx.shortest_path(
                self.graph, source=source, target=target, weight=weight, method=method
            )
        except nx.NetworkXNoPath as e:
            raise NoPathFoundError(f"No path from '{source}' to '{target}'") from e

    def shortest_simple_paths(
        self, source: str, target: str
    ) -> Generator[list[str], None, None]:
        """Generate simple paths from source to target, ordered by length.

        Args:
            source: The starting node.
            target: The target node.

        Yields:
            Paths from shortest to longest.

        Raises:
            NodeNotFoundError: If source or target is not in the graph.
        """
        self._validate_nodes(source, target)
        return nx.algorithms.simple_paths.shortest_simple_paths(
            self.graph, source=source, target=target
        )

    def find_cycle(self, start_node: str) -> list[tuple[str, str]]:
        """Find a cycle starting from a given node.

        Args:
            start_node: The node to start the cycle search from.

        Returns:
            List of edges forming the cycle.

        Raises:
            NodeNotFoundError: If the node is not in the graph.
            NoCycleFoundError: If no cycle is found from the given node.
        """
        self._validate_nodes(start_node)
        try:
            return nx.algorithms.cycles.find_cycle(self.graph, start_node)
        except nx.NetworkXNoCycle as e:
            raise NoCycleFoundError(f"No cycle found from '{start_node}'") from e

    def simple_cycles(self) -> Generator[list[str], None, None]:
        """Generate all simple cycles in the graph.

        Yields:
            Simple cycles as lists of nodes.
        """
        return nx.algorithms.cycles.simple_cycles(self.graph)

    def unique_cycles(self, *, show_progress: bool = True) -> list[list[tuple[str, str]]]:
        """Find all unique cycles in the graph.

        Args:
            show_progress: If True, show a progress bar.

        Returns:
            List of unique cycles, where each cycle is a list of edge tuples.
        """
        seen_hashes: set[int] = set()
        unique: list[list[tuple[str, str]]] = []

        iterator = tqdm(
            self.node_data["word"],
            desc="Finding cycles",
            disable=not show_progress,
            leave=False,
        )

        for word in iterator:
            try:
                cycle = self.find_cycle(word)
                cycle_hash = hash(str(cycle))
                if cycle_hash not in seen_hashes:
                    seen_hashes.add(cycle_hash)
                    unique.append(cycle)
            except NoCycleFoundError:
                continue

        return unique

    def strongly_connected_components(self) -> Generator[set[str], None, None]:
        """Generate the strongly connected components.

        Yields:
            Sets of nodes for each strongly connected component.
        """
        return nx.algorithms.components.strongly_connected_components(self.graph)

    def eulerian_circuit(self) -> list[tuple[str, str]]:
        """Get the Eulerian circuit of the graph.

        Returns:
            List of edges forming the Eulerian circuit.

        Raises:
            GraphNotEulerianError: If the graph is not Eulerian.
        """
        if not nx.is_eulerian(self.graph):
            raise GraphNotEulerianError("Graph does not have an Eulerian circuit")
        return list(nx.eulerian_circuit(self.graph))

    def volume(self, nodes: Sequence[str]) -> int:
        """Compute the volume of a subset of nodes.

        The volume is the sum of degrees of the nodes in the subset.

        Args:
            nodes: Sequence of node names.

        Returns:
            The volume of the node subset.
        """
        return nx.algorithms.cuts.volume(self.graph, nodes)

    # -------------------------------------------------------------------------
    # Graph Modification Methods
    # -------------------------------------------------------------------------

    def remove_self_loops(self) -> None:
        """Remove all self-loops from the graph (modifies in place)."""
        self.graph.remove_edges_from(nx.selfloop_edges(self.graph))

    def k_core(self, k: int | None = None) -> BiGramGraph:
        """Extract the k-core subgraph.

        The k-core is the maximal subgraph where all nodes have degree >= k.

        Args:
            k: The degree threshold. If None, uses the maximum core number.

        Returns:
            A new BiGramGraph representing the k-core.
        """
        k_core_graph = nx.algorithms.core.k_core(self.graph, k=k)
        return self._from_subgraph(k_core_graph)

    # -------------------------------------------------------------------------
    # NLP Enrichment Methods
    # -------------------------------------------------------------------------

    def enrich_pos(self, *, show_progress: bool = True) -> None:
        """Add part-of-speech tags to node data.

        Uses spaCy to extract POS tags for each word.

        Args:
            show_progress: If True, show a progress bar.
        """
        self._nlp = _get_nlp_model()

        if show_progress:
            tqdm.pandas(desc="Extracting POS tags")
            self.node_data["pos"] = self.node_data["word"].progress_apply(
                lambda w: self._nlp(str(w))[0].pos_
            )
        else:
            self.node_data["pos"] = self.node_data["word"].apply(
                lambda w: self._nlp(str(w))[0].pos_
            )

    def enrich_entities(self, *, show_progress: bool = True) -> None:
        """Add named entity tags to node data.

        Uses spaCy to extract entity labels for each word.

        Args:
            show_progress: If True, show a progress bar.
        """
        self._nlp = _get_nlp_model()

        def get_entity(word: str) -> str:
            entities = self._nlp(str(word)).ents
            return entities[0].label_ if entities else ""

        if show_progress:
            tqdm.pandas(desc="Extracting entities")
            self.node_data["entity"] = self.node_data["word"].progress_apply(get_entity)
        else:
            self.node_data["entity"] = self.node_data["word"].apply(get_entity)

    # -------------------------------------------------------------------------
    # Serialization Methods
    # -------------------------------------------------------------------------

    def save(self, path: str | Path) -> None:
        """Save the graph to a pickle file.

        Args:
            path: File path to save to (should end in .pkl).
        """
        with open(path, "wb") as f:
            pickle.dump(self.to_dict(), f)

    @classmethod
    def load(cls, path: str | Path) -> BiGramGraph:
        """Load a graph from a pickle file.

        Args:
            path: File path to load from.

        Returns:
            The loaded BiGramGraph instance.
        """
        with open(path, "rb") as f:
            state = pickle.load(f)
        return cls.from_dict(state)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the graph to a dictionary.

        Returns:
            Dictionary containing all graph state.
        """
        return {
            "graph": self.graph,
            "num_nodes": self.num_nodes,
            "num_edges": self.num_edges,
            "degree_stats": {
                "in_min": self.degree_stats.in_min,
                "in_max": self.degree_stats.in_max,
                "out_min": self.degree_stats.out_min,
                "out_max": self.degree_stats.out_max,
            },
            "node_data": self.node_data.to_dict(),
            "edge_data": self.edge_data.to_dict(),
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, state: dict[str, Any]) -> BiGramGraph:
        """Reconstruct a graph from a dictionary.

        Args:
            state: Dictionary containing graph state (from to_dict()).

        Returns:
            The reconstructed BiGramGraph instance.
        """
        # Create instance without calling __init__
        instance = object.__new__(cls)
        instance.graph = state["graph"]
        instance.num_nodes = state["num_nodes"]
        instance.num_edges = state["num_edges"]
        instance.degree_stats = DegreeStats(**state["degree_stats"])
        instance.node_data = pd.DataFrame(state["node_data"])
        instance.edge_data = pd.DataFrame(state["edge_data"])
        instance.name = state["name"]
        instance._nlp = None
        return instance

    # -------------------------------------------------------------------------
    # Private Helper Methods
    # -------------------------------------------------------------------------

    def _validate_nodes(self, *nodes: str) -> None:
        """Validate that all nodes exist in the graph."""
        for node in nodes:
            if node not in self.graph.nodes:
                raise NodeNotFoundError(f"Node '{node}' not found in graph")

    def _from_subgraph(self, subgraph: nx.DiGraph) -> BiGramGraph:
        """Create a new BiGramGraph from a subgraph."""
        nodes = list(subgraph.nodes())
        weights = dict(subgraph.edges)

        # Filter node data
        node_data = self.node_data[self.node_data["word"].isin(nodes)].copy()

        # Create edge data
        edge_data = pd.DataFrame(list(weights.keys()), columns=["source", "target"])
        if not edge_data.empty:
            edge_data["weight"] = edge_data.apply(
                lambda row: weights[(row["source"], row["target"])].get("weight", 1),
                axis=1,
            )
        else:
            edge_data["weight"] = pd.Series(dtype=float)

        # Create new instance
        instance = object.__new__(BiGramGraph)
        instance.graph = subgraph
        instance.num_nodes = subgraph.number_of_nodes()
        instance.num_edges = subgraph.number_of_edges()

        in_degrees = dict(subgraph.in_degree).values()
        out_degrees = dict(subgraph.out_degree).values()
        instance.degree_stats = DegreeStats(
            in_min=min(in_degrees) if in_degrees else 0,
            in_max=max(in_degrees) if in_degrees else 0,
            out_min=min(out_degrees) if out_degrees else 0,
            out_max=max(out_degrees) if out_degrees else 0,
        )

        instance.node_data = node_data.reset_index(drop=True)
        instance.edge_data = edge_data
        instance.name = self.name
        instance._nlp = None

        return instance

    # -------------------------------------------------------------------------
    # Dunder Methods
    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        """Return a string representation of the graph."""
        return (
            f"BiGramGraph(name='{self.name}', "
            f"nodes={self.num_nodes}, "
            f"edges={self.num_edges}, "
            f"chromatic_number={self.chromatic_number})"
        )

    def __len__(self) -> int:
        """Return the number of nodes in the graph."""
        return self.num_nodes

    def __contains__(self, word: str) -> bool:
        """Check if a word exists in the graph."""
        return word in self.graph.nodes

    def __getitem__(self, word: str) -> dict[str, Any]:
        """Get node attributes by word.

        Args:
            word: The word to look up.

        Returns:
            Dictionary of node attributes (color, pos, entity if available).

        Raises:
            NodeNotFoundError: If the word is not in the graph.
        """
        if word not in self.graph.nodes:
            raise NodeNotFoundError(f"Node '{word}' not found in graph")

        row = self.node_data[self.node_data["word"] == word]
        return row.to_dict(orient="records")[0] if not row.empty else {}
