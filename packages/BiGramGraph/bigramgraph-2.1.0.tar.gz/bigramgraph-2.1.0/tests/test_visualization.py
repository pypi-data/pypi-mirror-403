"""Tests for visualization functions."""

import tempfile
from pathlib import Path

import pytest

from BiGramGraph import BiGramGraph
from BiGramGraph.visualization import visualize, visualize_subgraph


class TestVisualize:
    """Tests for the visualize function."""

    def test_visualize_creates_file(self, sample_graph: BiGramGraph) -> None:
        """Test visualization creates an HTML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_graph.html"
            result = visualize(sample_graph, output_path=output_path)

            assert Path(result).exists()
            assert result.endswith(".html")

    def test_visualize_directed(self, sample_graph: BiGramGraph) -> None:
        """Test directed visualization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "directed.html"
            result = visualize(sample_graph, output_path=output_path, directed=True)
            assert Path(result).exists()

    def test_visualize_undirected(self, sample_graph: BiGramGraph) -> None:
        """Test undirected visualization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "undirected.html"
            result = visualize(sample_graph, output_path=output_path, directed=False)
            assert Path(result).exists()

    def test_visualize_dimensions(self, sample_graph: BiGramGraph) -> None:
        """Test custom dimensions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "sized.html"
            result = visualize(
                sample_graph,
                output_path=output_path,
                height=800,
                width=1200,
            )
            assert Path(result).exists()

    def test_visualize_no_physics(self, sample_graph: BiGramGraph) -> None:
        """Test visualization without physics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "no_physics.html"
            result = visualize(
                sample_graph,
                output_path=output_path,
                physics_enabled=False,
            )
            assert Path(result).exists()

    def test_visualize_show_weights(self, sample_graph: BiGramGraph) -> None:
        """Test visualization with edge weights shown."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "weights.html"
            result = visualize(
                sample_graph,
                output_path=output_path,
                show_weights=True,
            )
            assert Path(result).exists()


class TestVisualizeSubgraph:
    """Tests for the visualize_subgraph function."""

    def test_visualize_subgraph(self, sample_graph: BiGramGraph) -> None:
        """Test subgraph visualization."""
        # Get first few words
        words = list(sample_graph.node_data["word"][:5])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subgraph.html"
            result = visualize_subgraph(
                sample_graph,
                nodes=words,
                output_path=output_path,
            )
            assert Path(result).exists()

    def test_visualize_subgraph_empty(self, sample_graph: BiGramGraph) -> None:
        """Test subgraph visualization with no nodes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "empty_subgraph.html"
            result = visualize_subgraph(
                sample_graph,
                nodes=[],
                output_path=output_path,
            )
            assert Path(result).exists()
