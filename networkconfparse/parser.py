"""Turn indented configuration text into a :class:`ConfigNode` tree."""

from __future__ import annotations

from .node import ConfigNode


def _leading_spaces(line: str) -> int:
    """Number of leading whitespace characters, tabs expanded to spaces."""
    expanded = line.expandtabs()
    return len(expanded) - len(expanded.lstrip())


def parse(text: str) -> ConfigNode:
    """Parse whitespace-indented configuration into a tree of nodes.

    The parser is intentionally network-OS agnostic: it makes no assumptions
    about a fixed indent width. A line is a child of the nearest preceding line
    with strictly less indentation, which handles IOS (1 space), NX-OS (2
    spaces), and inconsistent indentation alike.

    Blank lines are skipped. Returns a synthetic root node whose children are
    the top-level (column 0) configuration lines.
    """
    root = ConfigNode(text="", indent=-1, parent=None)
    # Stack of nodes that could still be a parent of upcoming lines, ordered by
    # increasing indentation. The root (indent -1) always anchors the bottom.
    stack: list[ConfigNode] = [root]

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

    return root
