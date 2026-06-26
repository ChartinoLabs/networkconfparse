"""The core data structure: a single line of configuration in the tree."""

from __future__ import annotations

import re
from collections.abc import Iterator

from .typedefs import Patterns, Predicate
from .utils import _as_list


class _Queryable:
    """Regex query behaviour shared by `Config` and `ConfigNode`.

    Subclasses expose their immediate child nodes via `_query_nodes`; the
    subtree traversal and lookup logic lives here once, so the whole
    configuration and any individual node are queried the same way.

    Every lookup accepts an optional ``pattern`` (a regular expression, matched
    with `matches`) and an optional ``where`` predicate. When
    both are given a node must satisfy both; when neither is given every node
    matches.
    """

    __slots__ = ()

    @property
    def _query_nodes(self) -> list[ConfigNode]:
        """The immediate child nodes this object queries over."""
        raise NotImplementedError

    def _matcher(
        self,
        pattern: str | re.Pattern[str] | None,
        where: Predicate | None,
    ) -> Predicate:
        """Combine an optional regex and predicate into a single test."""
        compiled = re.compile(pattern) if pattern is not None else None

        def test(node: ConfigNode) -> bool:
            if compiled is not None and not node.matches(compiled):
                return False
            return not (where is not None and not where(node))

        return test

    def walk(self) -> Iterator[ConfigNode]:
        """Yield every descendant node, depth-first (pre-order).

        The object itself is not yielded; iteration descends into the immediate
        child nodes in configuration order.
        """
        for node in self._query_nodes:
            yield node
            yield from node.walk()

    def find(
        self,
        pattern: str | re.Pattern[str] | None = None,
        *,
        where: Predicate | None = None,
    ) -> list[ConfigNode]:
        """Return all descendant nodes matching ``pattern`` and/or ``where``.

        Searches the entire subtree, not just immediate children.
        """
        test = self._matcher(pattern, where)
        return [node for node in self.walk() if test(node)]

    def find_one(
        self,
        pattern: str | re.Pattern[str] | None = None,
        *,
        where: Predicate | None = None,
    ) -> ConfigNode | None:
        """Return the first descendant matching ``pattern``/``where``, or ``None``.

        Searches the whole subtree in pre-order.
        """
        test = self._matcher(pattern, where)
        for node in self.walk():
            if test(node):
                return node
        return None

    def find_child(
        self,
        pattern: str | re.Pattern[str] | None = None,
        *,
        where: Predicate | None = None,
    ) -> ConfigNode | None:
        """Return the first immediate child matching ``pattern``/``where``.

        Only immediate children are considered, in configuration order; returns
        ``None`` if none match.
        """
        test = self._matcher(pattern, where)
        for node in self._query_nodes:
            if test(node):
                return node
        return None

    def has_child(
        self,
        pattern: str | re.Pattern[str] | None = None,
        *,
        where: Predicate | None = None,
    ) -> bool:
        """Return whether any immediate child matches ``pattern``/``where``."""
        return self.find_child(pattern, where=where) is not None

    def find_with_child(
        self,
        pattern: str | re.Pattern[str] | None,
        child: Patterns,
    ) -> list[ConfigNode]:
        """Return nodes matching ``pattern`` that have ``child`` as direct children.

        ``child`` is one regex or an iterable of them; every pattern must match
        some direct child (logical AND). Implemented with `find` and a
        ``where`` predicate.
        """
        children = _as_list(child)
        return self.find(
            pattern,
            where=lambda node: all(node.has_child(c) for c in children),
        )

    def find_with_descendant(
        self,
        pattern: str | re.Pattern[str] | None,
        descendant: Patterns,
    ) -> list[ConfigNode]:
        """Return nodes matching ``pattern`` with ``descendant`` anywhere below.

        ``descendant`` is one regex or an iterable of them; every pattern must
        match some descendant at any depth (logical AND). Implemented with
        `find` and a ``where`` predicate.
        """
        descendants = _as_list(descendant)
        return self.find(
            pattern,
            where=lambda node: all(node.find_one(d) is not None for d in descendants),
        )

    def find_with_parent(
        self,
        pattern: str | re.Pattern[str] | None,
        parent: Patterns,
    ) -> list[ConfigNode]:
        """Return nodes matching ``pattern`` whose direct parent matches ``parent``.

        ``parent`` is one regex or an iterable of them; every pattern must match
        the single parent line (logical AND). Implemented with `find` and
        a ``where`` predicate.
        """
        parents = _as_list(parent)
        return self.find(
            pattern,
            where=lambda node: _parent_matches_all(node, parents),
        )

    def find_with_ancestor(
        self,
        pattern: str | re.Pattern[str] | None,
        ancestor: Patterns,
        *,
        adjacent: bool = False,
    ) -> list[ConfigNode]:
        """Return nodes matching ``pattern`` with ``ancestor`` above them.

        ``ancestor`` is one regex or an iterable of them, all required (AND).
        With ``adjacent=False`` (the default) each pattern must match some
        ancestor, in any order. With ``adjacent=True`` the patterns must form a
        consecutive chain matched nearest-first: the first against the direct
        parent, the next against its parent, and so on. Implemented with
        `find` and a ``where`` predicate.
        """
        ancestors = _as_list(ancestor)
        if adjacent:
            return self.find(
                pattern,
                where=lambda node: _adjacent_ancestors(node, ancestors),
            )
        return self.find(
            pattern,
            where=lambda node: _any_ancestor_each(node, ancestors),
        )


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
    def ancestors(self) -> Iterator[ConfigNode]:
        """Yield this node's ancestors, nearest parent first up to the top."""
        node = self.parent
        while node is not None:
            yield node
            node = node.parent

    @property
    def descendants(self) -> Iterator[ConfigNode]:
        """Yield every descendant, depth-first - equivalent to `walk`."""
        return self.walk()

    @property
    def root(self) -> ConfigNode:
        """Return the top-level line this node belongs to (itself if top-level)."""
        node = self
        while node.parent is not None:
            node = node.parent
        return node

    @property
    def path(self) -> list[str]:
        """The chain of ancestor lines down to this one, top-most first.

        For ``ip address ...`` nested under an interface this returns
        ``["interface Gi0/0", "ip address ..."]``. A top-level line's path is
        just its own text.
        """
        chain = [self.text]
        chain.extend(ancestor.text for ancestor in self.ancestors)
        chain.reverse()
        return chain

    def matches(self, pattern: str | re.Pattern[str]) -> bool:
        """Return whether this node's text matches ``pattern``.

        ``pattern`` may be a string (treated as a regular expression) or a
        pre-compiled pattern. Matching uses `re.search`, so the pattern
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


def _parent_matches_all(
    node: ConfigNode,
    patterns: list[str | re.Pattern[str]],
) -> bool:
    """Whether the node's direct parent matches every pattern."""
    parent = node.parent
    return parent is not None and all(parent.matches(p) for p in patterns)


def _adjacent_ancestors(
    node: ConfigNode,
    patterns: list[str | re.Pattern[str]],
) -> bool:
    """Whether the node's ancestry matches ``patterns`` as a consecutive chain.

    Patterns are matched nearest-first: the first against the node's direct
    parent, the next against that parent's parent, and so on with no gaps.
    """
    current = node.parent
    for pattern in patterns:
        if current is None or not current.matches(pattern):
            return False
        current = current.parent
    return True


def _any_ancestor_each(
    node: ConfigNode,
    patterns: list[str | re.Pattern[str]],
) -> bool:
    """Whether every pattern matches some ancestor, in any order."""
    ancestors = list(node.ancestors)
    return all(any(ancestor.matches(p) for ancestor in ancestors) for p in patterns)
