"""The core data structure: a single line of configuration in the tree."""

from __future__ import annotations

import re
from collections.abc import Iterator


class ConfigNode:
    """One line of configuration and its place in the hierarchy.

    Every node knows its own (stripped) text, its parent, and its children.
    A configuration is represented as a tree of these nodes hanging off a
    synthetic root node whose ``text`` is empty and whose ``parent`` is ``None``.
    """

    __slots__ = ("text", "indent", "parent", "children")

    def __init__(
        self,
        text: str,
        indent: int,
        parent: ConfigNode | None = None,
    ) -> None:
        """Create a node from its text, indentation depth, and parent."""
        self.text = text
        self.indent = indent
        self.parent = parent
        self.children: list[ConfigNode] = []

    @property
    def is_root(self) -> bool:
        """True for the synthetic top-level node that owns the whole tree."""
        return self.parent is None

    @property
    def path(self) -> list[str]:
        """The chain of ancestor lines down to this one, top-most first.

        Excludes the synthetic root. For ``ip address ...`` nested under an
        interface this returns ``["interface Gi0/0", "ip address ..."]``.
        """
        chain: list[str] = []
        node: ConfigNode | None = self
        while node is not None and not node.is_root:
            chain.append(node.text)
            node = node.parent
        chain.reverse()
        return chain

    def matches(self, pattern: str | re.Pattern[str]) -> bool:
        """Return whether this node's text matches ``pattern``.

        ``pattern`` may be a string (treated as a regular expression) or a
        pre-compiled pattern. Matching uses :func:`re.search`, so the pattern
        need not be anchored to match anywhere in the line.
        """
        return re.search(pattern, self.text) is not None

    def walk(self) -> Iterator[ConfigNode]:
        """Yield every descendant of this node, depth-first (pre-order).

        The node itself is not yielded; iteration descends into children in
        configuration order.
        """
        for child in self.children:
            yield child
            yield from child.walk()

    def find(self, pattern: str | re.Pattern[str]) -> list[ConfigNode]:
        """Return all descendants whose text matches ``pattern``.

        Searches the entire subtree, not just direct children. See
        :meth:`matches` for the matching semantics.
        """
        compiled = re.compile(pattern)
        return [node for node in self.walk() if node.matches(compiled)]

    def find_child(self, pattern: str | re.Pattern[str]) -> ConfigNode | None:
        """Return the first direct child matching ``pattern``, or ``None``.

        Only direct children are considered, in configuration order.
        """
        compiled = re.compile(pattern)
        for child in self.children:
            if child.matches(compiled):
                return child
        return None

    def has_child(self, pattern: str | re.Pattern[str]) -> bool:
        """Return whether any direct child matches ``pattern``."""
        return self.find_child(pattern) is not None

    def __iter__(self) -> Iterator[ConfigNode]:
        """Iterating a node yields its direct children."""
        return iter(self.children)

    def __len__(self) -> int:
        """Return the number of direct children."""
        return len(self.children)

    def __repr__(self) -> str:
        """Return a concise, debugging-friendly representation."""
        if self.is_root:
            return f"ConfigNode(<root>, children={len(self.children)})"
        return f"ConfigNode({self.text!r}, children={len(self.children)})"
