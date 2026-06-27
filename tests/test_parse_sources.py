"""Tests for the input forms accepted by `parse` (text, paths, files, lines)."""

import io
from pathlib import Path

import pytest

from networkconfparse import Config, parse

_CONFIG = (
    "interface GigabitEthernet0/0\n ip address 10.0.0.1 255.255.255.0\n no shutdown\n"
)


def _interface(config: Config) -> list[str]:
    """Flatten the canonical fixture to ``[parent, *children]`` text."""
    intf = config.nodes[0]
    return [intf.text, *(child.text for child in intf.children)]


def test_multiline_string_is_config_text() -> None:
    """A string containing a newline is always treated as configuration text."""
    config = parse(_CONFIG)
    assert _interface(config) == [
        "interface GigabitEthernet0/0",
        "ip address 10.0.0.1 255.255.255.0",
        "no shutdown",
    ]


def test_carriage_return_string_is_config_text() -> None:
    """The newline check covers a carriage return too, never tasting CR text."""
    text = "hostname r1\rip routing"
    config = parse(text)
    assert [n.text for n in config] == ["hostname r1", "ip routing"]


def test_tasted_path_that_exists_is_read(tmp_path: Path) -> None:
    """A newline-free string naming an existing file reads that file."""
    config_file = tmp_path / "router.cfg"
    config_file.write_text(_CONFIG, encoding="utf-8")
    config = parse(str(config_file))
    assert _interface(config)[0] == "interface GigabitEthernet0/0"


def test_tasted_path_that_is_missing_falls_back_to_text() -> None:
    """A newline-free string that names no file is parsed as single-line text."""
    config = parse("hostname r1")
    assert [n.text for n in config] == ["hostname r1"]


def test_tasting_is_exception_safe_for_overlong_string() -> None:
    """A string too long to be a path falls back to configuration text."""
    text = "x" * 100_000
    config = parse(text)
    assert [n.text for n in config] == [text]


def test_tasting_is_exception_safe_for_embedded_null() -> None:
    """A string with an embedded null falls back to configuration text."""
    text = "hostname\x00r1"
    config = parse(text)
    assert [n.text for n in config] == [text]


def test_directory_name_falls_back_to_text(tmp_path: Path) -> None:
    """Only an existing file triggers a read; a directory name is text."""
    config = parse(str(tmp_path))
    assert [n.text for n in config] == [str(tmp_path)]


def test_path_object_is_read(tmp_path: Path) -> None:
    """A `Path` is always a filesystem path and its contents are read."""
    config_file = tmp_path / "router.cfg"
    config_file.write_text(_CONFIG, encoding="utf-8")
    config = parse(config_file)
    assert _interface(config)[0] == "interface GigabitEthernet0/0"


def test_path_object_missing_raises() -> None:
    """A missing `Path` raises, never falling back to text."""
    with pytest.raises(FileNotFoundError):
        parse(Path("/does/not/exist/router.cfg"))


def test_file_like_object_is_read() -> None:
    """An open file-like object has its contents read."""
    config = parse(io.StringIO(_CONFIG))
    assert _interface(config)[0] == "interface GigabitEthernet0/0"


def test_binary_file_like_object_is_decoded(tmp_path: Path) -> None:
    """A file opened in binary mode is read and decoded as UTF-8."""
    config_file = tmp_path / "router.cfg"
    config_file.write_text(_CONFIG, encoding="utf-8")
    with config_file.open("rb") as handle:
        config = parse(handle)
    assert _interface(config)[0] == "interface GigabitEthernet0/0"


def test_line_iterable_without_trailing_newlines() -> None:
    """A list of lines with no trailing newlines is joined and parsed."""
    config = parse(
        [
            "interface GigabitEthernet0/0",
            " ip address 10.0.0.1 255.255.255.0",
            " no shutdown",
        ]
    )
    assert _interface(config) == [
        "interface GigabitEthernet0/0",
        "ip address 10.0.0.1 255.255.255.0",
        "no shutdown",
    ]


def test_line_iterable_with_trailing_newlines() -> None:
    """``readlines()``-style lines (with terminators) parse identically."""
    config = parse(
        [
            "interface GigabitEthernet0/0\n",
            " ip address 10.0.0.1 255.255.255.0\n",
            " no shutdown\n",
        ]
    )
    assert _interface(config) == [
        "interface GigabitEthernet0/0",
        "ip address 10.0.0.1 255.255.255.0",
        "no shutdown",
    ]


def test_generator_of_lines() -> None:
    """A generator of lines is consumed and parsed."""
    config = parse(line for line in ("hostname r1", "ip routing"))
    assert [n.text for n in config] == ["hostname r1", "ip routing"]


def test_empty_string_is_empty_config() -> None:
    """An empty string parses to a configuration with no lines."""
    assert len(parse("")) == 0


def test_empty_line_iterable_is_empty_config() -> None:
    """An empty iterable of lines parses to a configuration with no lines."""
    assert len(parse([])) == 0


def test_single_line_matching_a_filename_is_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The documented footgun: a single line matching a real file is read."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "hostname r1").write_text("ip routing\n", encoding="utf-8")
    # The bare string matches an existing file, so the file is read instead of
    # being treated as the single-line config "hostname r1".
    config = parse("hostname r1")
    assert [n.text for n in config] == ["ip routing"]


def test_trailing_newline_escape_hatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Appending a newline forces literal-text interpretation of a filename."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "hostname r1").write_text("ip routing\n", encoding="utf-8")
    config = parse("hostname r1\n")
    assert [n.text for n in config] == ["hostname r1"]
