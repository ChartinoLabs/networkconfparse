"""Tests for the Config wrapper returned by parse."""

from networkconfparse import Config, parse

SAMPLE = """\
hostname r1
interface Gi0/0
 ip address 10.0.0.1 255.255.255.0
"""


def test_parse_returns_config() -> None:
    """``parse`` returns a Config instance."""
    assert isinstance(parse(SAMPLE), Config)


def test_len_and_iter_cover_top_level_lines() -> None:
    """A configuration's length and iteration reflect its top-level lines."""
    config = parse(SAMPLE)
    assert len(config) == 2
    assert [n.text for n in config] == ["hostname r1", "interface Gi0/0"]


def test_nodes_exposes_top_level_lines() -> None:
    """The ``nodes`` attribute holds the ordered top-level lines."""
    config = parse(SAMPLE)
    assert config.nodes[0].text == "hostname r1"
    assert config.nodes[0].parent is None


def test_find_searches_the_whole_tree() -> None:
    """``find`` on a configuration descends into nested lines."""
    config = parse(SAMPLE)
    found = config.find(r"^ip address ")
    assert [n.text for n in found] == ["ip address 10.0.0.1 255.255.255.0"]


def test_find_child_only_top_level() -> None:
    """``find_child`` on a configuration matches only top-level lines."""
    config = parse(SAMPLE)
    hostname = config.find_child(r"^hostname ")
    assert hostname is not None
    assert hostname.text == "hostname r1"
    assert config.find_child(r"^ip address ") is None


def test_repr_reports_line_count() -> None:
    """A configuration's repr reports its top-level line count."""
    assert repr(parse(SAMPLE)) == "Config(lines=2)"
