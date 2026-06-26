"""Turn indented configuration text into a :class:`Config` of node trees."""

from __future__ import annotations

from .config import Config
from .node import ConfigNode


def _leading_spaces(line: str) -> int:
    """Number of leading whitespace characters, tabs expanded to spaces."""
    expanded = line.expandtabs()
    return len(expanded) - len(expanded.lstrip())


def parse(text: str) -> Config:
    """Parse whitespace-indented configuration into a :class:`Config`.

    The parser is intentionally network-OS agnostic: it makes no assumptions
    about a fixed indent width. A line is a child of the nearest preceding line
    with strictly less indentation, which handles IOS (1 space), NX-OS (2
    spaces), and inconsistent indentation alike.

    Blank lines are skipped. Returns a :class:`Config` wrapping the top-level
    (column 0) lines; each line's children are the lines indented beneath it.
    """
    # A throwaway sentinel anchors the parent stack during construction so that
    # top-level lines have something to attach to. It is never exposed: its
    # children are detached into the returned Config below.
    sentinel = ConfigNode(text="", indent=-1, parent=None)
    stack: list[ConfigNode] = [sentinel]

    for raw in text.splitlines():
        if not raw.strip():
            continue

        indent = _leading_spaces(raw)

        # Pop any nodes at the same or deeper indentation; they cannot be the
        # parent of this line.
        while stack[-1].indent >= indent:
            stack.pop()

        parent = stack[-1]
        node = ConfigNode(text=raw.strip(), indent=indent, parent=parent)
        parent.children.append(node)
        stack.append(node)

    top_level = sentinel.children
    for node in top_level:
        node.parent = None
    return Config(top_level)
