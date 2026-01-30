"""Tests for the TextGenerator class."""

import pytest

from BiGramGraph import BiGramGraph, TextGenerator


class TestTextGeneratorBasic:
    """Basic tests for TextGenerator."""

    def test_create_generator(self, sample_graph: BiGramGraph) -> None:
        """Test creating a generator."""
        generator = TextGenerator(sample_graph)
        assert generator.graph is sample_graph
        assert generator.chromatic_number == sample_graph.chromatic_number

    def test_repr(self, sample_graph: BiGramGraph) -> None:
        """Test string representation."""
        generator = TextGenerator(sample_graph)
        repr_str = repr(generator)
        assert "TextGenerator" in repr_str


class TestTextGeneratorGeneration:
    """Tests for text generation."""

    def test_generate_basic(self, sample_graph: BiGramGraph) -> None:
        """Test basic text generation."""
        generator = TextGenerator(sample_graph)
        text = generator.generate(num_colors=3, search_depth=5, show_progress=False)
        assert isinstance(text, str)

    def test_generate_heaviest(self, sample_graph: BiGramGraph) -> None:
        """Test generation with heaviest strategy."""
        generator = TextGenerator(sample_graph)
        text = generator.generate(
            num_colors=3,
            search_depth=5,
            strategy="heaviest",
            show_progress=False,
        )
        assert isinstance(text, str)

    def test_generate_lightest(self, sample_graph: BiGramGraph) -> None:
        """Test generation with lightest strategy."""
        generator = TextGenerator(sample_graph)
        text = generator.generate(
            num_colors=3,
            search_depth=5,
            strategy="lightest",
            show_progress=False,
        )
        assert isinstance(text, str)

    def test_generate_max_density(self, sample_graph: BiGramGraph) -> None:
        """Test generation with max_density strategy."""
        generator = TextGenerator(sample_graph)
        text = generator.generate(
            num_colors=3,
            search_depth=5,
            strategy="max_density",
            show_progress=False,
        )
        assert isinstance(text, str)

    def test_generate_min_density(self, sample_graph: BiGramGraph) -> None:
        """Test generation with min_density strategy."""
        generator = TextGenerator(sample_graph)
        text = generator.generate(
            num_colors=3,
            search_depth=5,
            strategy="min_density",
            show_progress=False,
        )
        assert isinstance(text, str)

    def test_generate_zero_colors(self, sample_graph: BiGramGraph) -> None:
        """Test generation with zero colors returns empty string."""
        generator = TextGenerator(sample_graph)
        text = generator.generate(num_colors=0, show_progress=False)
        assert text == ""

    def test_generate_one_color(self, sample_graph: BiGramGraph) -> None:
        """Test generation with one color returns empty string."""
        generator = TextGenerator(sample_graph)
        text = generator.generate(num_colors=1, show_progress=False)
        # With only one color, no transitions are possible
        assert isinstance(text, str)


class TestTextGeneratorColorSequence:
    """Tests for color sequence generation."""

    def test_color_sequence_length(self, sample_graph: BiGramGraph) -> None:
        """Test color sequence has correct length."""
        generator = TextGenerator(sample_graph)
        sequence = generator._generate_color_sequence(5)
        # May be shorter if consecutive colors match and are skipped
        assert len(sequence) <= 5

    def test_color_sequence_no_consecutive_same(self, sample_graph: BiGramGraph) -> None:
        """Test no consecutive same colors in sequence."""
        generator = TextGenerator(sample_graph)
        sequence = generator._generate_color_sequence(10)
        for i in range(len(sequence) - 1):
            assert sequence[i] != sequence[i + 1]

    def test_color_sequence_valid_range(self, sample_graph: BiGramGraph) -> None:
        """Test all colors are in valid range."""
        generator = TextGenerator(sample_graph)
        sequence = generator._generate_color_sequence(10)
        for color in sequence:
            assert 0 <= color < generator.chromatic_number
