"""Turn indented configuration text into a `Config` of node trees."""

from __future__ import annotations

from collections.abc import Callable

from .config import Config
from .node import ConfigNode


def _leading_spaces(line: str) -> int:
    """Number of leading whitespace characters, tabs expanded to spaces."""
    expanded = line.expandtabs()
    return len(expanded) - len(expanded.lstrip())


# Lines beginning with this marker are comments or section delimiters across
# Cisco IOS / IOS XE / IOS XR / NX-OS and carry no configuration semantics.
_COMMENT_PREFIX = "!"


def _is_comment(line: str) -> bool:
    """Whether a stripped line is a comment or section delimiter."""
    return line.startswith(_COMMENT_PREFIX)


# A banner command looks like ``banner <type> <delimiter>`` (e.g. ``banner motd
# ^C``); the multiline body that follows runs until the delimiter reappears.
_BANNER_PREFIX = "banner "
_MIN_BANNER_TOKENS = 3  # "banner", <type>, <delimiter>


def _banner_body_delimiter(line: str) -> str | None:
    """Return the delimiter that closes a multiline banner body, or ``None``.

    Returns ``None`` for non-banner lines and for single-line banners (where the
    delimiter appears twice on the same line, leaving no separate body to
    consume). Otherwise returns the trailing delimiter token.
    """
    if not line.startswith(_BANNER_PREFIX):
        return None
    tokens = line.split()
    if len(tokens) < _MIN_BANNER_TOKENS:
        return None
    delimiter = tokens[-1]
    head = line[: line.rfind(delimiter)]
    if delimiter in head:  # closing delimiter already present: single-line banner
        return None
    return delimiter


def _banner_terminator(delimiter: str) -> Callable[[str], str | None]:
    """Build a block terminator that closes a banner at ``delimiter``."""

    def terminator(line: str) -> str | None:
        if delimiter in line:
            return line[: line.index(delimiter)]
        return None

    return terminator


# Inline certificate data appears as a ``certificate <type> <serial>`` line whose
# hex body, indented beneath it, runs until a standalone ``quit``. The context
# guard ensures only certificates within a chain trigger body consumption.
_CERTIFICATE_PREFIX = "certificate "
_CERTIFICATE_CONTEXT = "certificate chain"
_CERTIFICATE_TERMINATOR = "quit"


def _is_certificate_start(line: str, parent: ConfigNode) -> bool:
    """Whether ``line`` opens inline certificate data within a cert chain."""
    in_chain = _CERTIFICATE_CONTEXT in parent.text
    return in_chain and line.startswith(_CERTIFICATE_PREFIX)


def _certificate_terminator(line: str) -> str | None:
    """Close a certificate block at a standalone ``quit`` line."""
    if line.strip() == _CERTIFICATE_TERMINATOR:
        return ""
    return None


def _consume_block(
    lines: list[str],
    start: int,
    parent: ConfigNode,
    terminator: Callable[[str], str | None],
) -> int:
    """Attach verbatim body lines as children of ``parent`` until ``terminator``.

    Returns the index of the first line after the block. Body lines are stored
    verbatim because their whitespace is content rather than structure. The
    terminator line is dropped, though any body text it carries is kept.
    """
    body_indent = parent.indent + 1
    index = start
    while index < len(lines):
        line = lines[index]
        trailing = terminator(line)
        if trailing is not None:
            if trailing:
                child = ConfigNode(text=trailing, indent=body_indent, parent=parent)
                parent.children.append(child)
            return index + 1
        child = ConfigNode(text=line, indent=body_indent, parent=parent)
        parent.children.append(child)
        index += 1
    return index  # unterminated block: consumed to end of input


def _consume_special_block(
    lines: list[str],
    index: int,
    node: ConfigNode,
    parent: ConfigNode,
) -> int | None:
    """Consume a banner or certificate body opened by ``node``, if any.

    Returns the index of the first line after the consumed block, or ``None`` if
    ``node`` does not open such a block.
    """
    delimiter = _banner_body_delimiter(node.text)
    if delimiter is not None:
        return _consume_block(lines, index + 1, node, _banner_terminator(delimiter))
    if _is_certificate_start(node.text, parent):
        return _consume_block(lines, index + 1, node, _certificate_terminator)
    return None


def parse(text: str) -> Config:
    """Parse whitespace-indented configuration into a `Config`.

    The parser is intentionally network-OS agnostic: it makes no assumptions
    about a fixed indent width. A line is a child of the nearest preceding line
    with strictly less indentation, which handles IOS (1 space), NX-OS (2
    spaces), and inconsistent indentation alike.

    Blank lines and comment/delimiter lines (those beginning with ``!``) are
    skipped, since the latter are redundant with indentation and carry no
    configuration semantics. Multiline ``banner`` blocks and inline certificate
    data (a ``certificate`` line within a ``certificate chain``, ended by
    ``quit``) are recognised and their bodies captured verbatim as children, so
    the freeform body is never mistaken for configuration.

    Returns a `Config` wrapping the top-level (column 0) lines; each
    line's children are the lines indented beneath it.
    """
    # A throwaway sentinel anchors the parent stack during construction so that
    # top-level lines have something to attach to. It is never exposed: its
    # children are detached into the returned Config below.
    sentinel = ConfigNode(text="", indent=-1, parent=None)
    stack: list[ConfigNode] = [sentinel]

    lines = text.splitlines()
    index = 0
    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()
        if not stripped or _is_comment(stripped):
            index += 1
            continue

        indent = _leading_spaces(raw)

        # Pop any nodes at the same or deeper indentation; they cannot be the
        # parent of this line.
        while stack[-1].indent >= indent:
            stack.pop()

        parent = stack[-1]
        node = ConfigNode(text=stripped, indent=indent, parent=parent)
        parent.children.append(node)

        consumed = _consume_special_block(lines, index, node, parent)
        if consumed is not None:
            # Banners and certificate chains own their freeform body, not
            # indentation-based children, so they are never pushed on the stack.
            index = consumed
            continue

        stack.append(node)
        index += 1

    top_level = sentinel.children
    for node in top_level:
        node.parent = None
    return Config(top_level)
