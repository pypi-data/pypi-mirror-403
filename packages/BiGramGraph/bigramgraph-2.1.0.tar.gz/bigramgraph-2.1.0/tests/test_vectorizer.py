"""Tests for the Vectorizer class."""

import numpy as np
import pytest

from BiGramGraph import BiGramGraph, Vectorizer


class TestVectorizerBasic:
    """Basic tests for Vectorizer."""

    def test_create_vectorizer(self, sample_graph: BiGramGraph) -> None:
        """Test creating a vectorizer."""
        vectorizer = Vectorizer(sample_graph)
        assert vectorizer.graph is sample_graph

    def test_vocabulary_size(self, sample_graph: BiGramGraph) -> None:
        """Test vocabulary size matches graph nodes."""
        vectorizer = Vectorizer(sample_graph)
        assert vectorizer.vocabulary_size == sample_graph.num_nodes

    def test_num_colors(self, sample_graph: BiGramGraph) -> None:
        """Test num_colors matches chromatic number."""
        vectorizer = Vectorizer(sample_graph)
        assert vectorizer.num_colors == sample_graph.chromatic_number


class TestVectorizerTransform:
    """Tests for single text transformation."""

    def test_transform_basic(self, sample_graph: BiGramGraph) -> None:
        """Test basic text transformation."""
        vectorizer = Vectorizer(sample_graph)
        vec = vectorizer.transform("the quick")
        assert isinstance(vec, np.ndarray)
        assert vec.ndim == 1
        assert len(vec) == 2

    def test_transform_known_word(self, sample_graph: BiGramGraph) -> None:
        """Test known words get valid colors."""
        vectorizer = Vectorizer(sample_graph)
        vec = vectorizer.transform("the")
        assert len(vec) == 1
        assert not np.isnan(vec[0])
        assert vec[0] >= 1  # Colors start at 1

    def test_transform_unknown_word(self, sample_graph: BiGramGraph) -> None:
        """Test unknown words get NaN."""
        vectorizer = Vectorizer(sample_graph)
        vec = vectorizer.transform("xyznonexistent")
        assert len(vec) == 1
        assert np.isnan(vec[0])

    def test_transform_mixed(self, sample_graph: BiGramGraph) -> None:
        """Test mixed known and unknown words."""
        vectorizer = Vectorizer(sample_graph)
        vec = vectorizer.transform("the xyzunknown quick")
        assert len(vec) == 3
        assert not np.isnan(vec[0])  # "the" is known
        assert np.isnan(vec[1])  # unknown word
        assert not np.isnan(vec[2])  # "quick" is known

    def test_transform_empty(self, sample_graph: BiGramGraph) -> None:
        """Test empty string returns empty array."""
        vectorizer = Vectorizer(sample_graph)
        vec = vectorizer.transform("")
        assert len(vec) == 0  # Empty string has no words


class TestVectorizerBatch:
    """Tests for batch transformation."""

    def test_transform_batch_basic(self, sample_graph: BiGramGraph) -> None:
        """Test basic batch transformation."""
        vectorizer = Vectorizer(sample_graph)
        vecs = vectorizer.transform_batch(["the quick", "brown fox"])
        assert isinstance(vecs, np.ndarray)
        assert vecs.ndim == 2
        assert vecs.shape[0] == 2  # Two texts

    def test_transform_batch_padding(self, sample_graph: BiGramGraph) -> None:
        """Test batch transformation pads to max length."""
        vectorizer = Vectorizer(sample_graph)
        vecs = vectorizer.transform_batch(
            ["the", "the quick brown"],
            pad_value=0.0,
        )
        assert vecs.shape[1] == 3  # Padded to longest
        assert vecs[0, 1] == 0.0  # First text is padded
        assert vecs[0, 2] == 0.0

    def test_transform_batch_max_length(self, sample_graph: BiGramGraph) -> None:
        """Test batch transformation with explicit max_length."""
        vectorizer = Vectorizer(sample_graph)
        vecs = vectorizer.transform_batch(
            ["the quick brown fox"],
            max_length=10,
            pad_value=-1.0,
        )
        assert vecs.shape[1] == 10
        # First 4 positions should be filled, rest should be padding
        assert vecs[0, 9] == -1.0

    def test_transform_batch_empty_list(self, sample_graph: BiGramGraph) -> None:
        """Test batch transformation with empty list."""
        vectorizer = Vectorizer(sample_graph)
        vecs = vectorizer.transform_batch([])
        assert vecs.shape == (0, 0)


class TestVectorizerInverse:
    """Tests for inverse transformation."""

    def test_inverse_transform_basic(self, sample_graph: BiGramGraph) -> None:
        """Test inverse transformation returns possible words."""
        vectorizer = Vectorizer(sample_graph)

        # First transform a known word
        vec = vectorizer.transform("the")
        inverse = vectorizer.inverse_transform(vec)

        assert isinstance(inverse, list)
        assert len(inverse) > 0
        # The original word should be among possibilities
        possible_words = inverse[0]
        assert "the" in possible_words

    def test_inverse_transform_nan(self, sample_graph: BiGramGraph) -> None:
        """Test inverse transformation with NaN values."""
        vectorizer = Vectorizer(sample_graph)

        vec = np.array([np.nan])
        inverse = vectorizer.inverse_transform(vec, skip_nan=True)
        assert inverse == []  # Skipped NaN

        inverse_with_nan = vectorizer.inverse_transform(vec, skip_nan=False)
        assert inverse_with_nan[0] == ["<UNK>"]
