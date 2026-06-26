"""Tests for skipping ! comment and section-delimiter lines."""

from networkconfparse import parse


def test_bare_delimiters_between_sections_are_dropped() -> None:
    """Bare ``!`` lines separating top-level sections do not become nodes."""
    cfg = (
        "interface Gi0/0\n"
        " ip address 10.0.0.1 255.255.255.0\n"
        "!\n"
        "interface Gi0/1\n"
        " shutdown\n"
        "!\n"
    )
    config = parse(cfg)
    assert [n.text for n in config] == ["interface Gi0/0", "interface Gi0/1"]
    assert len(config) == 2


def test_delimiters_within_a_block_are_dropped() -> None:
    """``!`` lines between children do not disturb the surviving children."""
    cfg = "router bgp 100\n neighbor 1.1.1.1\n !\n neighbor 2.2.2.2\n"
    config = parse(cfg)
    bgp = config.nodes[0]
    assert [c.text for c in bgp.children] == ["neighbor 1.1.1.1", "neighbor 2.2.2.2"]


def test_indented_iosxr_style_block_closers_are_dropped() -> None:
    """Indented ``!`` block-closers (IOS XR style) leave the tree intact."""
    cfg = "router ospf 1\n area 0\n  interface Gi0/0/0/0\n  !\n !\n!\nrouter bgp 100\n"
    config = parse(cfg)
    assert [n.text for n in config] == ["router ospf 1", "router bgp 100"]
    area = config.nodes[0].children[0]
    assert area.text == "area 0"
    assert [c.text for c in area.children] == ["interface Gi0/0/0/0"]


def test_comment_lines_with_text_are_dropped() -> None:
    """A ``! comment text`` line is treated as a comment and skipped."""
    cfg = "! this is a comment\nhostname r1\n ! nested comment\n logging on\n"
    config = parse(cfg)
    assert [n.text for n in config] == ["hostname r1"]
    assert [c.text for c in config.nodes[0].children] == ["logging on"]


def test_bang_mid_line_is_preserved() -> None:
    """A ``!`` that is not at the start of the line is kept as ordinary text."""
    cfg = "interface Gi0/0\n description has!bang in it\n"
    config = parse(cfg)
    assert config.nodes[0].children[0].text == "description has!bang in it"


def test_queries_work_on_comment_laden_config() -> None:
    """End-to-end queries ignore comments and return only real config."""
    cfg = (
        "!\n"
        "interface Gi0/0\n"
        " ip address 10.0.0.1 255.255.255.0\n"
        "!\n"
        "interface Gi0/1\n"
        " shutdown\n"
        "!\n"
    )
    config = parse(cfg)
    with_ip = config.find_with_child(r"^interface ", r"^ip address ")
    assert [n.text for n in with_ip] == ["interface Gi0/0"]
