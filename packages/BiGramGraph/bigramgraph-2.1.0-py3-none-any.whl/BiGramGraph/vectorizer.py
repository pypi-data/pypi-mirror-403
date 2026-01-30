"""Text vectorization using BiGramGraph chromatic coloring.

This module provides the Vectorizer class for converting text to numerical
vectors based on the chromatic coloring of a BiGramGraph.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from BiGramGraph.core import BiGramGraph


class Vectorizer:
    """Convert text to numerical vectors using chromatic coloring.

    The vectorizer maps each word to its chromatic color number in the graph.
    Words not found in the graph are mapped to NaN.

    Attributes:
        graph: The BiGramGraph used for vectorization.

    Example:
        >>> graph = BiGramGraph(["the quick brown fox"])
        >>> vectorizer = Vectorizer(graph)
        >>> vec = vectorizer.transform("the quick")
        >>> print(vec)  # [1. 2.]
    """

    def __init__(self, graph: BiGramGraph) -> None:
        """Initialize the vectorizer with a BiGramGraph.

        Args:
            graph: The BiGramGraph to use for vectorization.
        """
        self.graph = graph
        # Build lookup dict for fast access
        self._color_map: dict[str, int] = dict(
            zip(graph.node_data["word"], graph.node_data["color"])
        )

    def transform(self, text: str) -> np.ndarray:
        """Transform a single text string to a vector.

        Each word is mapped to its chromatic color number + 1 (so colors start at 1).
        Unknown words are mapped to NaN.

        Args:
            text: The text string to vectorize.

        Returns:
            1D numpy array of chromatic color values.

        Example:
            >>> vec = vectorizer.transform("hello world")
        """
        words = text.split()
        result = np.empty(len(words), dtype=np.float64)

        for i, word in enumerate(words):
            if word in self._color_map:
                result[i] = self._color_map[word] + 1
            else:
                result[i] = np.nan

        return result

    def transform_batch(
        self,
        texts: Sequence[str],
        *,
        max_length: int | None = None,
        pad_value: float = 0.0,
    ) -> np.ndarray:
        """Transform a batch of texts to a 2D array.

        All texts are padded to the same length (either max_length or the
        length of the longest text).

        Args:
            texts: Sequence of text strings to vectorize.
            max_length: Maximum sequence length. If None, uses the length
                of the longest text.
            pad_value: Value to use for padding shorter sequences.

        Returns:
            2D numpy array of shape (num_texts, max_length).

        Example:
            >>> vecs = vectorizer.transform_batch(
            ...     ["hello world", "foo"],
            ...     max_length=5,
            ...     pad_value=0
            ... )
        """
        # Determine output length
        lengths = [len(text.split()) for text in texts]
        if max_length is None:
            max_length = max(lengths) if lengths else 0

        # Initialize output array with padding
        result = np.full((len(texts), max_length), pad_value, dtype=np.float64)

        # Fill in the values
        for i, text in enumerate(texts):
            words = text.split()
            for j, word in enumerate(words):
                if j >= max_length:
                    break
                if word in self._color_map:
                    result[i, j] = self._color_map[word] + 1
                else:
                    result[i, j] = np.nan

        return result

    def inverse_transform(
        self,
        vector: np.ndarray,
        *,
        skip_nan: bool = True,
    ) -> list[list[str]]:
        """Convert vectors back to possible words.

        Since multiple words can have the same color, this returns all
        possible words for each position.

        Args:
            vector: 1D or 2D array of chromatic color values.
            skip_nan: If True, skip NaN values in the output.

        Returns:
            Nested list where each element contains possible words
            for that position.
        """
        # Build inverse lookup
        inverse_map: dict[int, list[str]] = {}
        for word, color in self._color_map.items():
            color_val = color + 1
            if color_val not in inverse_map:
                inverse_map[color_val] = []
            inverse_map[color_val].append(word)

        # Handle 1D input
        if vector.ndim == 1:
            vector = vector.reshape(1, -1)

        results = []
        for row in vector:
            row_result = []
            for val in row:
                if np.isnan(val):
                    if not skip_nan:
                        row_result.append(["<UNK>"])
                else:
                    color_int = int(val)
                    row_result.append(inverse_map.get(color_int, ["<UNK>"]))
            results.append(row_result)

        return results if len(results) > 1 else results[0]

    @property
    def vocabulary_size(self) -> int:
        """Number of unique words in the vocabulary."""
        return len(self._color_map)

    @property
    def num_colors(self) -> int:
        """Number of unique colors (chromatic number)."""
        return self.graph.chromatic_number
