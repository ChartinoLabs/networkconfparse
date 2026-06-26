"""Tests for node navigation conveniences: ancestors, descendants, root."""

from networkconfparse import parse

NESTED = "policy-map PM\n class CM\n  police 8000\n   conform-action transmit\n"


def test_ancestors_yields_nearest_parent_first() -> None:
    """``ancestors`` walks up the tree from the nearest parent to the top."""
    config = parse(NESTED)
    conform = config.nodes[0].children[0].children[0].children[0]
    assert [a.text for a in conform.ancestors] == [
        "police 8000",
        "class CM",
        "policy-map PM",
    ]


def test_top_level_node_has_no_ancestors() -> None:
    """A top-level line has an empty ancestor chain."""
    config = parse("hostname r1\n")
    assert list(config.nodes[0].ancestors) == []


def test_descendants_matches_walk() -> None:
    """``descendants`` yields the same nodes as ``walk`` in the same order."""
    config = parse(NESTED)
    pm = config.nodes[0]
    assert [n.text for n in pm.descendants] == [n.text for n in pm.walk()]
    assert [n.text for n in pm.descendants] == [
        "class CM",
        "police 8000",
        "conform-action transmit",
    ]


def test_root_returns_top_level_line() -> None:
    """``root`` returns the top-level line a deep node belongs to."""
    config = parse(NESTED)
    conform = config.nodes[0].children[0].children[0].children[0]
    assert conform.root.text == "policy-map PM"


def test_root_of_top_level_node_is_itself() -> None:
    """A top-level line is its own root."""
    config = parse("hostname r1\n")
    node = config.nodes[0]
    assert node.root is node
