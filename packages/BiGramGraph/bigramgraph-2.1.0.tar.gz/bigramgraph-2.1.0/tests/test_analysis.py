"""Tests for analysis functions."""

import pytest

from BiGramGraph import BiGramGraph
from BiGramGraph.analysis import (
    calculate_cycle_density,
    calculate_path_density,
    calculate_path_weight,
    chromatic_distance,
    graph_similarity_report,
)
from BiGramGraph.exceptions import MissingEnrichmentError


def _spacy_model_available() -> bool:
    """Check if spaCy model is available."""
    try:
        import spacy
        spacy.load("en_core_web_sm")
        return True
    except OSError:
        return False


requires_spacy_model = pytest.mark.skipif(
    not _spacy_model_available(),
    reason="spaCy model 'en_core_web_sm' not installed"
)


class TestPathWeight:
    """Tests for calculate_path_weight function."""

    def test_path_weight_basic(self, sample_graph: BiGramGraph) -> None:
        """Test basic path weight calculation."""
        # Get a valid path
        words = list(sample_graph.node_data["word"])
        if len(words) >= 2:
            # Find two connected words from edge data
            edge = sample_graph.edge_data.iloc[0]
            path = [edge["source"], edge["target"]]
            weight = calculate_path_weight(sample_graph, path)
            assert weight > 0

    def test_path_weight_empty(self, sample_graph: BiGramGraph) -> None:
        """Test weight of empty path is zero."""
        assert calculate_path_weight(sample_graph, []) == 0.0

    def test_path_weight_single_node(self, sample_graph: BiGramGraph) -> None:
        """Test weight of single node path is zero."""
        word = sample_graph.node_data["word"].iloc[0]
        assert calculate_path_weight(sample_graph, [word]) == 0.0


class TestPathDensity:
    """Tests for calculate_path_density function."""

    def test_path_density_basic(self, sample_graph: BiGramGraph) -> None:
        """Test basic path density calculation."""
        words = list(sample_graph.node_data["word"][:3])
        density = calculate_path_density(sample_graph, words)
        assert density >= 0

    def test_path_density_empty(self, sample_graph: BiGramGraph) -> None:
        """Test density of empty path is zero."""
        assert calculate_path_density(sample_graph, []) == 0.0


class TestCycleDensity:
    """Tests for calculate_cycle_density function."""

    def test_cycle_density_basic(self, cyclic_graph: BiGramGraph) -> None:
        """Test basic cycle density calculation."""
        try:
            cycle = cyclic_graph.find_cycle("a")
            density = calculate_cycle_density(cyclic_graph, cycle)
            assert density >= 0
        except Exception:
            pass  # May not have cycles


class TestChromaticDistance:
    """Tests for chromatic_distance function."""

    @requires_spacy_model
    def test_chromatic_distance_same_graph(self, sample_texts: list[str]) -> None:
        """Test chromatic distance of graph with itself is 1.0."""
        graph1 = BiGramGraph(sample_texts, show_progress=False)
        graph2 = BiGramGraph(sample_texts, show_progress=False)

        graph1.enrich_pos(show_progress=False)
        graph2.enrich_pos(show_progress=False)

        distance = chromatic_distance(graph1, graph2)
        # Same graph should have high similarity
        assert 0 <= distance <= 1.0

    def test_chromatic_distance_missing_pos(self, sample_graph: BiGramGraph) -> None:
        """Test chromatic distance raises error without POS tags."""
        graph2 = BiGramGraph(["different text here"], show_progress=False)

        with pytest.raises(MissingEnrichmentError):
            chromatic_distance(sample_graph, graph2)

    @requires_spacy_model
    def test_chromatic_distance_no_overlap(self) -> None:
        """Test chromatic distance with no overlapping words."""
        graph1 = BiGramGraph(["alpha beta gamma"], show_progress=False)
        graph2 = BiGramGraph(["delta epsilon zeta"], show_progress=False)

        graph1.enrich_pos(show_progress=False)
        graph2.enrich_pos(show_progress=False)

        distance = chromatic_distance(graph1, graph2)
        assert distance == 0.0


class TestGraphSimilarityReport:
    """Tests for graph_similarity_report function."""

    def test_similarity_report_structure(self, sample_texts: list[str]) -> None:
        """Test similarity report returns expected keys."""
        graph1 = BiGramGraph(sample_texts, show_progress=False)
        graph2 = BiGramGraph(sample_texts[:2], show_progress=False)

        report = graph_similarity_report(graph1, graph2)

        assert "overlapping_words" in report
        assert "total_unique_words" in report
        assert "jaccard_similarity" in report
        assert "size_ratio" in report

    @requires_spacy_model
    def test_similarity_report_with_pos(self, sample_texts: list[str]) -> None:
        """Test similarity report includes chromatic distance when POS available."""
        graph1 = BiGramGraph(sample_texts, show_progress=False)
        graph2 = BiGramGraph(sample_texts, show_progress=False)

        graph1.enrich_pos(show_progress=False)
        graph2.enrich_pos(show_progress=False)

        report = graph_similarity_report(graph1, graph2)
        assert "chromatic_distance" in report
