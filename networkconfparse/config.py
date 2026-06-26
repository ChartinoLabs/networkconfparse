"""High-level wrapper exposing query access over a parsed configuration."""

from __future__ import annotations

from collections.abc import Iterator

from .node import ConfigNode, _Queryable


class Config(_Queryable):
    """A parsed configuration: its ordered top-level lines and their subtrees.

    Returned by :func:`networkconfparse.parse`. A configuration owns the
    top-level lines (those at column 0). :meth:`find` searches the whole tree,
    while :meth:`find_child` and :meth:`has_child` consider only top-level
    lines.
    """

    __slots__ = ("nodes",)

    def __init__(self, nodes: list[ConfigNode]) -> None:
        """Create a configuration from its ordered top-level nodes."""
        self.nodes = nodes

    @property
    def _query_nodes(self) -> list[ConfigNode]:
        """A configuration queries over its top-level lines."""
        return self.nodes

    def __iter__(self) -> Iterator[ConfigNode]:
        """Iterating a configuration yields its top-level lines."""
        return iter(self.nodes)

    def __len__(self) -> int:
        """Return the number of top-level lines."""
        return len(self.nodes)

    def __repr__(self) -> str:
        """Return a concise, debugging-friendly representation."""
        return f"Config(lines={len(self.nodes)})"
