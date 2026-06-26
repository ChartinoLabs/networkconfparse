"""Tests for the indentation-based configuration parser."""

from networkconfparse import Config, ConfigNode, parse


def test_empty_config_has_no_nodes() -> None:
    """An empty string parses to a configuration with no lines."""
    config = parse("")
    assert isinstance(config, Config)
    assert list(config) == []
    assert len(config) == 0


def test_top_level_lines_become_parentless_nodes() -> None:
    """Unindented lines become top-level nodes with no parent."""
    config = parse("hostname r1\nip routing\n")
    assert [n.text for n in config] == ["hostname r1", "ip routing"]
    assert all(n.parent is None for n in config)


def test_single_space_indent_ios_style() -> None:
    """IOS single-space indentation nests lines under their parent."""
    cfg = (
        "interface GigabitEthernet0/0\n"
        " ip address 10.0.0.1 255.255.255.0\n"
        " no shutdown\n"
    )
    config = parse(cfg)

    assert len(config) == 1
    intf = config.nodes[0]
    assert intf.text == "interface GigabitEthernet0/0"
    assert [c.text for c in intf.children] == [
        "ip address 10.0.0.1 255.255.255.0",
        "no shutdown",
    ]
    assert all(c.parent is intf for c in intf.children)


def test_two_space_indent_nxos_style() -> None:
    """NX-OS two-space indentation nests lines under their parent."""
    cfg = "interface Ethernet1/1\n  switchport\n  switchport mode trunk\n"
    config = parse(cfg)
    intf = config.nodes[0]
    assert [c.text for c in intf.children] == ["switchport", "switchport mode trunk"]


def test_deep_nesting() -> None:
    """Lines nest to arbitrary depth as indentation increases."""
    cfg = "policy-map PM\n class CM\n  police 8000\n   conform-action transmit\n"
    config = parse(cfg)
    police = config.nodes[0].children[0].children[0]
    assert police.text == "police 8000"
    assert police.children[0].text == "conform-action transmit"


def test_dedent_returns_to_correct_parent() -> None:
    """Decreasing indentation reattaches following lines to the right parent."""
    cfg = (
        "interface Gi0/0\n"
        " ip address 10.0.0.1 255.255.255.0\n"
        "interface Gi0/1\n"
        " shutdown\n"
    )
    config = parse(cfg)
    assert len(config) == 2
    assert config.nodes[0].children[0].text == "ip address 10.0.0.1 255.255.255.0"
    assert config.nodes[1].children[0].text == "shutdown"


def test_path_walks_ancestors() -> None:
    """``path`` returns the ancestor chain from top-most line to this one."""
    cfg = "policy-map PM\n class CM\n  police 8000\n"
    config = parse(cfg)
    police = config.nodes[0].children[0].children[0]
    assert police.path == ["policy-map PM", "class CM", "police 8000"]


def test_top_level_path_is_just_itself() -> None:
    """A top-level line's path contains only its own text."""
    config = parse("hostname r1\n")
    assert config.nodes[0].path == ["hostname r1"]


def test_tabs_are_expanded() -> None:
    """Tab-indented lines are treated as indentation, not text."""
    cfg = "interface Gi0/0\n\tshutdown\n"
    config = parse(cfg)
    assert config.nodes[0].children[0].text == "shutdown"


def test_blank_lines_skipped() -> None:
    """Blank lines are ignored and do not appear in the tree."""
    config = parse("hostname r1\n\n\nip routing\n")
    assert [n.text for n in config] == ["hostname r1", "ip routing"]


def test_node_repr_and_iteration() -> None:
    """A node iterates over its children and reprs with its text."""
    config = parse("interface Gi0/0\n shutdown\n")
    intf = config.nodes[0]
    assert list(intf) == intf.children
    assert "interface Gi0/0" in repr(intf)
    assert isinstance(intf, ConfigNode)
