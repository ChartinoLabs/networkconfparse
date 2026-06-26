"""The core data structure: a single line of configuration in the tree."""

from __future__ import annotations

import re
from collections.abc import Iterator


class _Queryable:
    """Regex query behaviour shared by :class:`Config` and :class:`ConfigNode`.

    Subclasses expose their immediate child nodes via :attr:`_query_nodes`; the
    subtree traversal and lookup logic lives here once, so the whole
    configuration and any individual node are queried the same way.
    """

    __slots__ = ()

    @property
    def _query_nodes(self) -> list[ConfigNode]:
        """The immediate child nodes this object queries over."""
        raise NotImplementedError

    def walk(self) -> Iterator[ConfigNode]:
        """Yield every descendant node, depth-first (pre-order).

        The object itself is not yielded; iteration descends into the immediate
        child nodes in configuration order.
        """
        for node in self._query_nodes:
            yield node
            yield from node.walk()

    def find(self, pattern: str | re.Pattern[str]) -> list[ConfigNode]:
        """Return all descendant nodes whose text matches ``pattern``.

        Searches the entire subtree, not just immediate children. See
        :meth:`ConfigNode.matches` for the matching semantics.
        """
        compiled = re.compile(pattern)
        return [node for node in self.walk() if node.matches(compiled)]

    def find_child(self, pattern: str | re.Pattern[str]) -> ConfigNode | None:
        """Return the first immediate child matching ``pattern``, or ``None``.

        Only immediate children are considered, in configuration order.
        """
        compiled = re.compile(pattern)
        for node in self._query_nodes:
            if node.matches(compiled):
                return node
        return None

    def has_child(self, pattern: str | re.Pattern[str]) -> bool:
        """Return whether any immediate child matches ``pattern``."""
        return self.find_child(pattern) is not None


class ConfigNode(_Queryable):
    """One line of configuration and its place in the hierarchy.

    Every node knows its own (stripped) text, its parent, and its children.
    Top-level lines (those at column 0) have no parent; deeper lines point at
    the line they are indented beneath.
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
    def _query_nodes(self) -> list[ConfigNode]:
        """A node queries over its own direct children."""
        return self.children

    @property
    def path(self) -> list[str]:
        """The chain of ancestor lines down to this one, top-most first.

        For ``ip address ...`` nested under an interface this returns
        ``["interface Gi0/0", "ip address ..."]``. A top-level line's path is
        just its own text.
        """
        chain: list[str] = []
        node: ConfigNode | None = self
        while node is not None:
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

    def __iter__(self) -> Iterator[ConfigNode]:
        """Iterating a node yields its direct children."""
        return iter(self.children)

    def __len__(self) -> int:
        """Return the number of direct children."""
        return len(self.children)

    def __repr__(self) -> str:
        """Return a concise, debugging-friendly representation."""
        return f"ConfigNode({self.text!r}, children={len(self.children)})"
