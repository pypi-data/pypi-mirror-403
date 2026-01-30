"""Text generation using chromatic random walks.

This module provides the TextGenerator class for generating synthetic text
by performing random walks on a BiGramGraph following chromatic constraints.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import nltk
import numpy as np
from tqdm import tqdm

from BiGramGraph.analysis import calculate_path_density

if TYPE_CHECKING:
    from BiGramGraph.core import BiGramGraph


class TextGenerator:
    """Generate synthetic text using chromatic random walks on a bigram graph.

    This class uses the chromatic coloring of a BiGramGraph to generate
    text by walking through the graph following color-based constraints.

    The generation process:
    1. Generate a random sequence of chromatic colors
    2. For each color transition, find paths between words of those colors
    3. Select the best path based on the chosen strategy
    4. Concatenate the paths to form the generated text

    Attributes:
        graph: The underlying BiGramGraph instance.
        chromatic_number: The chromatic number of the graph.

    Example:
        >>> graph = BiGramGraph(texts)
        >>> generator = TextGenerator(graph)
        >>> text = generator.generate(num_colors=5, strategy="heaviest")
    """

    def __init__(self, graph: BiGramGraph) -> None:
        """Initialize the text generator with a BiGramGraph.

        Args:
            graph: The BiGramGraph to use for text generation.
        """
        self.graph = graph
        self.chromatic_number = graph.chromatic_number
        self._color_map: dict[str, int] = dict(
            zip(graph.node_data["word"], graph.node_data["color"])
        )

    def generate(
        self,
        *,
        num_colors: int = 5,
        search_depth: int = 10,
        strategy: Literal["heaviest", "lightest", "max_density", "min_density"] = "heaviest",
        show_progress: bool = True,
    ) -> str:
        """Generate synthetic text using chromatic random walks.

        Args:
            num_colors: Number of color transitions to make (affects output length).
            search_depth: Maximum number of target words to consider at each step.
            strategy: Path selection strategy:
                - 'heaviest': Select the path with maximum total edge weight
                - 'lightest': Select the path with minimum total edge weight
                - 'max_density': Select the path with maximum node degree density
                - 'min_density': Select the path with minimum node degree density
            show_progress: If True, show progress bars.

        Returns:
            Generated text string.
        """
        # Generate random chromatic color sequence
        color_sequence = self._generate_color_sequence(num_colors)

        if len(color_sequence) < 2:
            return ""

        # Start with a random word of the first color
        first_color = color_sequence[0]
        words_with_color = self.graph.node_data[
            self.graph.node_data["color"] == first_color
        ]
        current_word = words_with_color.sample(1)["word"].values[0]

        result_parts = []

        # Iterate through color transitions
        color_iter = tqdm(
            color_sequence[1:],
            desc="Generating text",
            disable=not show_progress,
        )

        for target_color in color_iter:
            # Get target words with the target color
            target_words = self.graph.node_data[
                self.graph.node_data["color"] == target_color
            ]
            sample_size = min(search_depth, len(target_words))
            target_words = target_words.sample(sample_size)

            # Find paths to each target
            paths: list[list[str]] = []
            for target in tqdm(target_words["word"], leave=False, disable=not show_progress):
                try:
                    path_gen = self.graph.shortest_simple_paths(current_word, target)
                    paths.append(next(path_gen))
                except (StopIteration, Exception):
                    continue

            if not paths:
                continue

            # Select best path based on strategy
            best_path, best_idx = self._select_best_path(paths, strategy)
            current_word = target_words["word"].values[best_idx]

            # Add path to result (excluding last word to avoid duplicates)
            if best_path:
                result_parts.append(" ".join(best_path[:-1]))

        return " ".join(result_parts).strip()

    def _generate_color_sequence(self, length: int) -> list[int]:
        """Generate a random sequence of chromatic colors.

        Uses a beta distribution to generate colors, ensuring no two
        consecutive colors are the same.

        Args:
            length: Desired length of the color sequence.

        Returns:
            List of chromatic color indices.
        """
        if self.chromatic_number == 0:
            return []

        colors = list(range(self.chromatic_number))
        sequence: list[int] = []
        last_color = -1

        for _ in range(length):
            # Use beta distribution for varied sampling
            max_attempts = 100
            for _ in range(max_attempts):
                index = int(np.floor(np.random.beta(1.5, 1.5) * self.chromatic_number))
                index = min(index, self.chromatic_number - 1)  # Clamp
                color = colors[index]

                if color != last_color:
                    sequence.append(color)
                    last_color = color
                    break

        return sequence

    def _select_best_path(
        self,
        paths: list[list[str]],
        strategy: str,
    ) -> tuple[list[str], int]:
        """Select the best path according to the given strategy.

        Args:
            paths: List of candidate paths.
            strategy: Selection strategy.

        Returns:
            Tuple of (best_path, index_of_best_path).
        """
        if not paths:
            return [], 0

        if strategy in ("heaviest", "lightest"):
            weights = [self._calculate_path_weight(p) for p in paths]
            if strategy == "heaviest":
                best_idx = int(np.argmax(weights))
            else:
                best_idx = int(np.argmin(weights))
        else:  # density strategies
            densities = [calculate_path_density(self.graph, p) for p in paths]
            if strategy == "max_density":
                best_idx = int(np.argmax(densities))
            else:
                best_idx = int(np.argmin(densities))

        return paths[best_idx], best_idx

    def _calculate_path_weight(self, path: list[str]) -> float:
        """Calculate total edge weight along a path.

        Args:
            path: List of node names forming the path.

        Returns:
            Sum of edge weights.
        """
        if len(path) < 2:
            return 0.0

        weight = 0.0
        for i in range(len(path) - 1):
            source, target = path[i], path[i + 1]
            mask = (
                (self.graph.edge_data["source"] == source) &
                (self.graph.edge_data["target"] == target)
            )
            matches = self.graph.edge_data[mask]
            if not matches.empty:
                weight += matches["weight"].values[0]

        return weight

    def __repr__(self) -> str:
        """Return string representation of the generator."""
        return f"TextGenerator(graph={self.graph.name}, chromatic_number={self.chromatic_number})"
