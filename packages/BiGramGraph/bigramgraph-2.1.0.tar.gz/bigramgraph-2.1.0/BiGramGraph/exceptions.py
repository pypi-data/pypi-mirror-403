"""Custom exceptions for BiGramGraph."""

from __future__ import annotations


class BiGramGraphError(Exception):
    """Base exception for BiGramGraph errors."""


class GraphNotEulerianError(BiGramGraphError):
    """Raised when an Eulerian circuit is requested but the graph is not Eulerian."""


class GraphNotConnectedError(BiGramGraphError):
    """Raised when an operation requires a connected graph but it is not."""


class NodeNotFoundError(BiGramGraphError):
    """Raised when a requested node is not found in the graph."""


class NoCycleFoundError(BiGramGraphError):
    """Raised when no cycle is found starting from a given node."""


class NoPathFoundError(BiGramGraphError):
    """Raised when no path exists between two nodes."""


class MissingEnrichmentError(BiGramGraphError):
    """Raised when an operation requires enrichment data that hasn't been computed."""
