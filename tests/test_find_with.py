"""Tests for the relationship helpers: find_with_child/descendant/parent/ancestor."""

from networkconfparse import parse

SAMPLE = """\
router bgp 65000
 address-family ipv4 unicast
  neighbor 10.0.0.1 activate
  neighbor 10.0.0.2 activate
 address-family vpnv4 unicast
  neighbor 10.0.0.1 activate
interface GigabitEthernet0/0
 ip address 10.0.0.1 255.255.255.0
 no shutdown
interface GigabitEthernet0/1
 shutdown
ip access-list extended PERMIT_WEB
 permit tcp any any eq 80
 deny ip any any
"""


def test_find_with_child_single() -> None:
    """``find_with_child`` returns nodes with a matching direct child."""
    config = parse(SAMPLE)
    found = config.find_with_child(r"^interface ", r"^ip address ")
    assert [n.text for n in found] == ["interface GigabitEthernet0/0"]


def test_find_with_child_anchors_distinguish_shutdown() -> None:
    """A direct child of ``shutdown`` excludes interfaces with ``no shutdown``."""
    config = parse(SAMPLE)
    found = config.find_with_child(r"^interface ", r"^shutdown")
    assert [n.text for n in found] == ["interface GigabitEthernet0/1"]


def test_find_with_child_list_is_and() -> None:
    """A list of child patterns must all match direct children."""
    config = parse(SAMPLE)
    found = config.find_with_child(
        r"^interface ",
        [r"^ip address ", r"^no shutdown"],
    )
    assert [n.text for n in found] == ["interface GigabitEthernet0/0"]


def test_find_with_child_pattern_optional() -> None:
    """A ``None`` target matches any node carrying the given child."""
    config = parse(SAMPLE)
    found = config.find_with_child(None, r"^ip address ")
    assert [n.text for n in found] == ["interface GigabitEthernet0/0"]


def test_find_with_descendant_searches_any_depth() -> None:
    """``find_with_descendant`` matches nested lines a child helper would miss."""
    config = parse(SAMPLE)
    found = config.find_with_descendant(r"^router bgp ", r"activate")
    assert [n.text for n in found] == ["router bgp 65000"]
    # The same target has no direct child matching ``activate``.
    assert config.find_with_child(r"^router bgp ", r"activate") == []


def test_find_with_descendant_list_is_and() -> None:
    """A list of descendant patterns must all match somewhere below."""
    config = parse(SAMPLE)
    found = config.find_with_descendant(r"^router bgp ", [r"activate", r"vpnv4"])
    assert [n.text for n in found] == ["router bgp 65000"]


def test_find_with_parent_single() -> None:
    """``find_with_parent`` matches nodes by their direct parent."""
    config = parse(SAMPLE)
    found = config.find_with_parent(r"activate", r"address-family ipv4")
    assert [n.text for n in found] == [
        "neighbor 10.0.0.1 activate",
        "neighbor 10.0.0.2 activate",
    ]


def test_find_with_parent_list_is_and() -> None:
    """A list of parent patterns must all match the single parent line."""
    config = parse(SAMPLE)
    found = config.find_with_parent(r"activate", [r"^address-family", r"ipv4"])
    assert [n.text for n in found] == [
        "neighbor 10.0.0.1 activate",
        "neighbor 10.0.0.2 activate",
    ]


def test_find_with_ancestor_order_independent() -> None:
    """Default ancestor matching requires each pattern somewhere above."""
    config = parse(SAMPLE)
    found = config.find_with_ancestor(
        r"activate",
        [r"router bgp", r"address-family ipv4"],
    )
    assert [n.text for n in found] == [
        "neighbor 10.0.0.1 activate",
        "neighbor 10.0.0.2 activate",
    ]


def test_find_with_ancestor_single_spans_all_depths() -> None:
    """A single ancestor pattern matches regardless of intervening levels."""
    config = parse(SAMPLE)
    found = config.find_with_ancestor(r"activate", r"router bgp")
    assert len(found) == 3


def test_find_with_ancestor_adjacent_requires_chain() -> None:
    """``adjacent=True`` matches a consecutive chain, nearest-first."""
    config = parse(SAMPLE)
    found = config.find_with_ancestor(
        r"activate",
        [r"address-family ipv4", r"router bgp"],
        adjacent=True,
    )
    assert [n.text for n in found] == [
        "neighbor 10.0.0.1 activate",
        "neighbor 10.0.0.2 activate",
    ]


def test_find_with_ancestor_adjacent_rejects_gap() -> None:
    """``adjacent=True`` rejects an ancestor that is not the direct parent."""
    config = parse(SAMPLE)
    # ``router bgp`` is a grandparent of activate, not its direct parent.
    assert config.find_with_ancestor(r"activate", r"router bgp", adjacent=True) == []


def test_find_with_ancestor_adjacent_respects_order() -> None:
    """``adjacent=True`` matches the list nearest-first, so order matters."""
    config = parse(SAMPLE)
    # Reversed order: nearest parent is the address-family, not ``router bgp``.
    assert (
        config.find_with_ancestor(
            r"activate",
            [r"router bgp", r"address-family ipv4"],
            adjacent=True,
        )
        == []
    )


def test_helpers_scope_to_a_subtree() -> None:
    """The helpers work on any node, scoping the search to its subtree."""
    config = parse(SAMPLE)
    bgp = config.find_one(r"^router bgp ")
    assert bgp is not None
    found = bgp.find_with_parent(r"activate", r"address-family vpnv4")
    assert [n.text for n in found] == ["neighbor 10.0.0.1 activate"]
