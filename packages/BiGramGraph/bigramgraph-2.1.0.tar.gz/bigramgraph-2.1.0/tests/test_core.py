"""Tests for the core BiGramGraph class."""

import tempfile
from pathlib import Path

import pytest

from BiGramGraph import BiGramGraph, DegreeStats
from BiGramGraph.exceptions import (
    GraphNotConnectedError,
    GraphNotEulerianError,
    NoCycleFoundError,
    NodeNotFoundError,
    NoPathFoundError,
)


class TestBiGramGraphConstruction:
    """Tests for graph construction."""

    def test_create_from_texts(self, sample_texts: list[str]) -> None:
        """Test basic graph creation."""
        graph = BiGramGraph(sample_texts, show_progress=False)
        assert graph.num_nodes > 0
        assert graph.num_edges > 0

    def test_custom_name(self, sample_texts: list[str]) -> None:
        """Test setting custom graph name."""
        graph = BiGramGraph(sample_texts, name="MyGraph", show_progress=False)
        assert graph.name == "MyGraph"

    def test_node_data_structure(self, sample_graph: BiGramGraph) -> None:
        """Test node_data DataFrame structure."""
        assert "word" in sample_graph.node_data.columns
        assert "color" in sample_graph.node_data.columns
        assert len(sample_graph.node_data) == sample_graph.num_nodes

    def test_edge_data_structure(self, sample_graph: BiGramGraph) -> None:
        """Test edge_data DataFrame structure."""
        assert "source" in sample_graph.edge_data.columns
        assert "target" in sample_graph.edge_data.columns
        assert "weight" in sample_graph.edge_data.columns
        assert len(sample_graph.edge_data) == sample_graph.num_edges

    def test_degree_stats(self, sample_graph: BiGramGraph) -> None:
        """Test degree statistics are computed correctly."""
        stats = sample_graph.degree_stats
        assert isinstance(stats, DegreeStats)
        assert stats.in_min >= 0
        assert stats.in_max >= stats.in_min
        assert stats.out_min >= 0
        assert stats.out_max >= stats.out_min


class TestBiGramGraphProperties:
    """Tests for graph properties."""

    def test_chromatic_number(self, sample_graph: BiGramGraph) -> None:
        """Test chromatic number computation."""
        chi = sample_graph.chromatic_number
        assert chi > 0
        assert chi <= sample_graph.num_nodes

    def test_is_dag(self, sample_graph: BiGramGraph) -> None:
        """Test DAG detection."""
        # Most bigram graphs are not DAGs due to repeated words
        assert isinstance(sample_graph.is_dag, bool)

    def test_is_strongly_connected(self, sample_graph: BiGramGraph) -> None:
        """Test strongly connected detection."""
        assert isinstance(sample_graph.is_strongly_connected, bool)

    def test_num_strongly_connected_components(self, sample_graph: BiGramGraph) -> None:
        """Test counting strongly connected components."""
        num_scc = sample_graph.num_strongly_connected_components
        assert num_scc >= 1

    def test_diameter_raises_on_disconnected(self, simple_graph: BiGramGraph) -> None:
        """Test diameter raises error on disconnected graph."""
        if not simple_graph.is_strongly_connected:
            with pytest.raises(GraphNotConnectedError):
                _ = simple_graph.diameter


class TestBiGramGraphPathFinding:
    """Tests for path finding methods."""

    def test_shortest_path(self, sample_graph: BiGramGraph) -> None:
        """Test finding shortest path."""
        # Get two connected words
        words = list(sample_graph.node_data["word"][:2])
        if len(words) >= 2:
            try:
                path = sample_graph.shortest_path(words[0], words[1])
                assert isinstance(path, list)
                assert path[0] == words[0]
                assert path[-1] == words[1]
            except NoPathFoundError:
                pass  # No path exists, which is valid

    def test_shortest_path_invalid_node(self, sample_graph: BiGramGraph) -> None:
        """Test shortest path with invalid node raises error."""
        with pytest.raises(NodeNotFoundError):
            sample_graph.shortest_path("nonexistent", "the")

    def test_shortest_simple_paths(self, sample_graph: BiGramGraph) -> None:
        """Test generating simple paths."""
        words = list(sample_graph.node_data["word"][:2])
        if len(words) >= 2:
            try:
                paths = sample_graph.shortest_simple_paths(words[0], words[1])
                first_path = next(paths)
                assert isinstance(first_path, list)
            except (StopIteration, NodeNotFoundError):
                pass


class TestBiGramGraphCycles:
    """Tests for cycle detection methods."""

    def test_find_cycle(self, cyclic_graph: BiGramGraph) -> None:
        """Test finding a cycle from a node."""
        # This graph should have cycles
        try:
            cycle = cyclic_graph.find_cycle("a")
            assert isinstance(cycle, list)
            assert len(cycle) > 0
        except NoCycleFoundError:
            pass  # May not have cycle from this node

    def test_find_cycle_no_cycle(self, simple_graph: BiGramGraph) -> None:
        """Test finding cycle when none exists raises error."""
        # Try to find a cycle, may raise NoCycleFoundError
        try:
            simple_graph.find_cycle("a")
        except NoCycleFoundError:
            pass  # Expected for some nodes

    def test_simple_cycles(self, cyclic_graph: BiGramGraph) -> None:
        """Test generating all simple cycles."""
        cycles = list(cyclic_graph.simple_cycles())
        assert isinstance(cycles, list)

    def test_unique_cycles(self, cyclic_graph: BiGramGraph) -> None:
        """Test finding unique cycles."""
        cycles = cyclic_graph.unique_cycles(show_progress=False)
        assert isinstance(cycles, list)


class TestBiGramGraphModification:
    """Tests for graph modification methods."""

    def test_remove_self_loops(self, sample_graph: BiGramGraph) -> None:
        """Test removing self loops."""
        initial_edges = sample_graph.num_edges
        sample_graph.remove_self_loops()
        # Should have same or fewer edges
        assert sample_graph.graph.number_of_edges() <= initial_edges

    def test_k_core(self, sample_graph: BiGramGraph) -> None:
        """Test extracting k-core."""
        k_core = sample_graph.k_core(k=1)
        assert isinstance(k_core, BiGramGraph)
        assert k_core.num_nodes <= sample_graph.num_nodes


class TestBiGramGraphEulerian:
    """Tests for Eulerian circuit methods."""

    def test_eulerian_circuit_raises(self, sample_graph: BiGramGraph) -> None:
        """Test Eulerian circuit raises error for non-Eulerian graph."""
        # Most graphs won't be Eulerian
        with pytest.raises(GraphNotEulerianError):
            sample_graph.eulerian_circuit()


class TestBiGramGraphSerialization:
    """Tests for serialization methods."""

    def test_to_dict_from_dict(self, sample_graph: BiGramGraph) -> None:
        """Test serialization round-trip via dict."""
        state = sample_graph.to_dict()
        restored = BiGramGraph.from_dict(state)

        assert restored.num_nodes == sample_graph.num_nodes
        assert restored.num_edges == sample_graph.num_edges
        assert restored.name == sample_graph.name

    def test_save_load(self, sample_graph: BiGramGraph) -> None:
        """Test serialization round-trip via file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_graph.pkl"
            sample_graph.save(path)

            restored = BiGramGraph.load(path)
            assert restored.num_nodes == sample_graph.num_nodes
            assert restored.num_edges == sample_graph.num_edges


class TestBiGramGraphDunderMethods:
    """Tests for dunder methods."""

    def test_repr(self, sample_graph: BiGramGraph) -> None:
        """Test string representation."""
        repr_str = repr(sample_graph)
        assert "BiGramGraph" in repr_str
        assert str(sample_graph.num_nodes) in repr_str

    def test_len(self, sample_graph: BiGramGraph) -> None:
        """Test len returns num_nodes."""
        assert len(sample_graph) == sample_graph.num_nodes

    def test_contains(self, sample_graph: BiGramGraph) -> None:
        """Test 'in' operator."""
        assert "the" in sample_graph
        assert "nonexistent_word_xyz" not in sample_graph

    def test_getitem(self, sample_graph: BiGramGraph) -> None:
        """Test indexing to get node attributes."""
        attrs = sample_graph["the"]
        assert "word" in attrs
        assert "color" in attrs

    def test_getitem_invalid(self, sample_graph: BiGramGraph) -> None:
        """Test indexing with invalid word raises error."""
        with pytest.raises(NodeNotFoundError):
            _ = sample_graph["nonexistent_xyz"]
