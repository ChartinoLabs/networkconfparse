"""Turn indented configuration text into a `Config` of node trees."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
from typing import IO, TypeAlias

from .config import Config
from .node import ConfigNode

# The input forms `parse` accepts: literal configuration text or a path-tasted
# string, an explicit filesystem `Path`, an open file-like object (text or
# binary), or an iterable of lines. See `parse` for the dispatch and
# string-tasting rules.
ConfigSource: TypeAlias = "str | Path | IO[str] | IO[bytes] | Iterable[str]"


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


_NEWLINES = ("\n", "\r")


def _taste_string(text: str) -> str:
    """Resolve a bare ``str`` to configuration text, reading it as a file if apt.

    A string containing a newline cannot be a filesystem path, so it is always
    returned unchanged as configuration text. A newline-free string is "tasted"
    against the filesystem: if it names an existing file, that file's UTF-8
    contents are returned; otherwise the string itself is returned as (unusual,
    single-line) configuration text.

    Tasting is exception-safe: any error from path handling (for example an
    over-long string raising ``OSError`` or an embedded null raising
    ``ValueError``) falls back to treating the input as configuration text.
    """
    if any(newline in text for newline in _NEWLINES):
        return text
    try:
        candidate = Path(text)
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8")
    except (OSError, ValueError):
        pass  # not a usable path: fall back to treating the input as text
    return text


def _line_to_text(line: str | bytes) -> str:
    """Normalise one line from an iterable to terminator-free text."""
    if isinstance(line, bytes):
        line = line.decode("utf-8")
    return line.rstrip("\r\n")


def _coerce_to_text(source: ConfigSource) -> str:
    """Reduce any accepted input form to a single configuration-text string.

    See `parse` for the dispatch table and the string-tasting rule.
    """
    if isinstance(source, Path):
        # An explicit Path is an unambiguous "this is a path" signal: it does
        # not fall back to text, so a missing path raises FileNotFoundError.
        return source.read_text(encoding="utf-8")
    if isinstance(source, str):
        return _taste_string(source)
    read = getattr(source, "read", None)
    if callable(read):  # file-like object
        contents = read()
        if isinstance(contents, bytes):
            return contents.decode("utf-8")
        return contents
    # Iterable of lines: join them, dropping any per-line terminators so that
    # both bare lines and ``readlines()`` output yield the same configuration.
    return "\n".join(_line_to_text(line) for line in source)


def parse(source: ConfigSource) -> Config:
    r"""Parse whitespace-indented configuration into a `Config`.

    The single entry point accepts the input forms callers commonly have on
    hand, dispatching on the type of ``source``:

    ===========================================  ===============================
    Input                                        Interpretation
    ===========================================  ===============================
    ``str`` containing a newline (``\n``/``\r``)   literal configuration text
    ``str`` without a newline                    tasted as a path (see below)
    `pathlib.Path`                               always a filesystem path
    file-like object (has ``.read()``)           its contents are read
    iterable of ``str`` (list/tuple/generator)   joined as lines
    ===========================================  ===============================

    String tasting: a bare ``str`` containing a newline cannot be a path, so it
    is always configuration text. A newline-free ``str`` is checked against the
    filesystem - if it resolves to an existing file, that file is read (as
    UTF-8); otherwise it is parsed as (unusual, single-line) configuration text.
    Tasting is exception-safe and only an existing file triggers a read, so a
    directory name falls back to text. As a documented footgun, a single-line
    config that happens to match an existing filename will be read as that file;
    to force literal-text interpretation, append a trailing newline. A
    `pathlib.Path` is an explicit path signal and never falls back: a missing
    path raises ``FileNotFoundError``.

    .. warning::

       Because tasting can read a file from a bare ``str``, do not pass an
       **untrusted** string to ``parse``: an attacker who controls the input
       could supply a path (for example ``/etc/passwd``) and have its contents
       read and returned through the parsed tree. When the source is untrusted,
       guarantee text interpretation by ensuring it contains a newline (append
       ``"\n"`` to a single-line value), or wrap it explicitly with
       `io.StringIO` before calling ``parse``.

    The parser itself is network-OS agnostic: it makes no assumptions about a
    fixed indent width. A line is a child of the nearest preceding line with
    strictly less indentation, which handles IOS (1 space), NX-OS (2 spaces),
    and inconsistent indentation alike.

    Blank lines and comment/delimiter lines (those beginning with ``!``) are
    skipped, since the latter are redundant with indentation and carry no
    configuration semantics. Multiline ``banner`` blocks and inline certificate
    data (a ``certificate`` line within a ``certificate chain``, ended by
    ``quit``) are recognised and their bodies captured verbatim as children, so
    the freeform body is never mistaken for configuration.

    Returns a `Config` wrapping the top-level (column 0) lines; each
    line's children are the lines indented beneath it.
    """
    return _parse_text(_coerce_to_text(source))


def _parse_text(text: str) -> Config:
    """Build the node tree from already-resolved configuration text."""
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
