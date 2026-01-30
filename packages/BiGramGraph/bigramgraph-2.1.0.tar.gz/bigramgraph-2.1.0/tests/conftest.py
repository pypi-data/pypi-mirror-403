"""Pytest fixtures for BiGramGraph tests."""

import pytest

from BiGramGraph import BiGramGraph


@pytest.fixture
def sample_texts() -> list[str]:
    """Simple sample texts for testing."""
    return [
        "the quick brown fox jumps over the lazy dog",
        "the dog runs fast",
        "quick fox is clever",
    ]


@pytest.fixture
def sample_graph(sample_texts: list[str]) -> BiGramGraph:
    """Create a sample BiGramGraph for testing."""
    return BiGramGraph(sample_texts, show_progress=False)


@pytest.fixture
def simple_texts() -> list[str]:
    """Minimal texts for basic tests."""
    return ["a b c", "b c d", "c d a"]


@pytest.fixture
def simple_graph(simple_texts: list[str]) -> BiGramGraph:
    """Create a simple graph with known structure."""
    return BiGramGraph(simple_texts, show_progress=False)


@pytest.fixture
def cyclic_texts() -> list[str]:
    """Texts that create a cyclic graph."""
    return ["a b c a", "b c a b"]


@pytest.fixture
def cyclic_graph(cyclic_texts: list[str]) -> BiGramGraph:
    """Create a graph with known cycles."""
    return BiGramGraph(cyclic_texts, show_progress=False)
