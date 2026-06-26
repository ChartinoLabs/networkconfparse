"""Turn indented configuration text into a :class:`Config` of node trees."""

from __future__ import annotations

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


def _consume_banner(
    lines: list[str],
    start: int,
    banner: ConfigNode,
    delimiter: str,
) -> int:
    """Attach banner body lines as children until ``delimiter``, return next index.

    Body lines are stored verbatim because their whitespace is content rather
    than structure. The closing delimiter line is dropped, though any text
    preceding the delimiter on that line is kept as a final body line.
    """
    body_indent = banner.indent + 1
    index = start
    while index < len(lines):
        line = lines[index]
        if delimiter in line:
            before = line[: line.index(delimiter)]
            if before:
                banner.children.append(
                    ConfigNode(text=before, indent=body_indent, parent=banner)
                )
            return index + 1
        banner.children.append(ConfigNode(text=line, indent=body_indent, parent=banner))
        index += 1
    return index  # unterminated banner: consumed to end of input


def parse(text: str) -> Config:
    """Parse whitespace-indented configuration into a :class:`Config`.

    The parser is intentionally network-OS agnostic: it makes no assumptions
    about a fixed indent width. A line is a child of the nearest preceding line
    with strictly less indentation, which handles IOS (1 space), NX-OS (2
    spaces), and inconsistent indentation alike.

    Blank lines and comment/delimiter lines (those beginning with ``!``) are
    skipped, since the latter are redundant with indentation and carry no
    configuration semantics. Multiline ``banner`` blocks are recognised and
    their body captured verbatim as children of the banner line, so the freeform
    body is never mistaken for configuration.

    Returns a :class:`Config` wrapping the top-level (column 0) lines; each
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

        delimiter = _banner_body_delimiter(stripped)
        if delimiter is not None:
            # A banner owns its freeform body, not indentation-based children, so
            # it is never pushed onto the stack.
            index = _consume_banner(lines, index + 1, node, delimiter)
            continue

        stack.append(node)
        index += 1

    top_level = sentinel.children
    for node in top_level:
        node.parent = None
    return Config(top_level)
