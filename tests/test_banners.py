"""Tests for multiline banner block parsing."""

from networkconfparse import parse


def test_banner_body_becomes_children_not_top_level() -> None:
    """Banner body lines attach to the banner node, not the config root."""
    cfg = (
        "hostname r1\n"
        "banner motd ^C\n"
        "  ****************************\n"
        "  * Unauthorized access!     *\n"
        "  ****************************\n"
        "^C\n"
        "interface Gi0/0\n"
        " ip address 10.0.0.1 255.255.255.0\n"
    )
    config = parse(cfg)
    assert [n.text for n in config] == [
        "hostname r1",
        "banner motd ^C",
        "interface Gi0/0",
    ]
    banner = config.nodes[1]
    assert [c.text for c in banner.children] == [
        "  ****************************",
        "  * Unauthorized access!     *",
        "  ****************************",
    ]


def test_banner_body_that_looks_like_config_is_not_parsed() -> None:
    """Config-looking and ``!`` lines inside a banner stay banner body."""
    cfg = (
        "banner motd ^C\n"
        "interface Gi0/0 is not a real interface\n"
        "!\n"
        "^C\n"
        "interface Gi0/1\n"
        " ip address 10.0.0.2 255.255.255.0\n"
    )
    config = parse(cfg)
    # Only the real interface is a top-level node.
    assert [n.text for n in config] == ["banner motd ^C", "interface Gi0/1"]
    # The fake interface and the ! both survived as verbatim banner body.
    banner = config.nodes[0]
    assert [c.text for c in banner.children] == [
        "interface Gi0/0 is not a real interface",
        "!",
    ]
    # Queries see only the genuine interface.
    real = config.find_with_child(r"^interface ", r"^ip address ")
    assert [n.text for n in real] == ["interface Gi0/1"]


def test_banner_with_hash_delimiter() -> None:
    """An operator-chosen ``#`` delimiter is honoured."""
    cfg = "banner login #\nLine A\nLine B\n#\nhostname r1\n"
    config = parse(cfg)
    assert [n.text for n in config] == ["banner login #", "hostname r1"]
    assert [c.text for c in config.nodes[0].children] == ["Line A", "Line B"]


def test_closing_delimiter_on_a_text_line() -> None:
    """Text preceding the closing delimiter on its line is kept."""
    cfg = "banner motd ^C\nWelcome^C\nhostname r1\n"
    config = parse(cfg)
    assert [n.text for n in config] == ["banner motd ^C", "hostname r1"]
    assert [c.text for c in config.nodes[0].children] == ["Welcome"]


def test_blank_lines_in_banner_body_are_preserved() -> None:
    """Blank lines inside a banner are content and are kept verbatim."""
    cfg = "banner motd ^C\nLine 1\n\nLine 3\n^C\nhostname r1\n"
    config = parse(cfg)
    assert [c.text for c in config.nodes[0].children] == ["Line 1", "", "Line 3"]
    assert config.nodes[1].text == "hostname r1"


def test_single_line_banner_stays_a_plain_node() -> None:
    """A banner that opens and closes on one line has no body children."""
    cfg = "banner exec ^C Keep it short ^C\nhostname r1\n"
    config = parse(cfg)
    assert [n.text for n in config] == [
        "banner exec ^C Keep it short ^C",
        "hostname r1",
    ]
    assert config.nodes[0].children == []


def test_unterminated_banner_consumes_to_end() -> None:
    """A banner with no closing delimiter consumes the remaining input."""
    cfg = "banner motd ^C\nforever\nand ever\n"
    config = parse(cfg)
    assert [n.text for n in config] == ["banner motd ^C"]
    assert [c.text for c in config.nodes[0].children] == ["forever", "and ever"]


def test_banner_is_findable_and_body_does_not_break_queries() -> None:
    """The banner line is queryable and surrounding config parses normally."""
    cfg = (
        "banner motd ^C\n"
        "Authorized users only\n"
        "^C\n"
        "interface Gi0/0\n"
        " ip address 10.0.0.1 255.255.255.0\n"
        " no shutdown\n"
    )
    config = parse(cfg)
    banner = config.find_one(r"^banner motd")
    assert banner is not None
    assert banner.children[0].text == "Authorized users only"
    interfaces = config.find_with_child(r"^interface ", r"^ip address ")
    assert [n.text for n in interfaces] == ["interface Gi0/0"]
