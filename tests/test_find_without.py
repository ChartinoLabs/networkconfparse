"""Tests for the negative relationship helpers: find_without_*.

Each finder is the NOR complement of its `find_with_*` counterpart: a node
matches when *none* of the given relationship patterns are present.
"""

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


def test_find_without_child_single() -> None:
    """``find_without_child`` returns nodes lacking a matching direct child."""
    config = parse(SAMPLE)
    found = config.find_without_child(r"^interface ", r"^ip address ")
    assert [n.text for n in found] == ["interface GigabitEthernet0/1"]


def test_find_without_child_anchors_distinguish_shutdown() -> None:
    """Interfaces without ``shutdown`` include one with ``no shutdown``."""
    config = parse(SAMPLE)
    found = config.find_without_child(r"^interface ", r"^shutdown")
    assert [n.text for n in found] == ["interface GigabitEthernet0/0"]


def test_find_without_child_list_is_nor() -> None:
    """A node lacking *every* listed child qualifies; partial matches excluded."""
    config = parse(SAMPLE)
    # Neither interface has both a description and a vrf, but Gi0/0 lacks both
    # of these absent patterns, so under NOR both interfaces qualify.
    found = config.find_without_child(
        r"^interface ",
        [r"^description ", r"^vrf "],
    )
    assert [n.text for n in found] == [
        "interface GigabitEthernet0/0",
        "interface GigabitEthernet0/1",
    ]


def test_find_without_child_partial_match_excluded() -> None:
    """Having some but not all listed children excludes a node (NOR)."""
    config = parse(SAMPLE)
    # Gi0/0 has ``ip address`` but not ``shutdown``; because one of the two is
    # present it is excluded. Gi0/1 has ``shutdown`` but no ``ip address`` and
    # is likewise excluded. So no interface lacks *both*.
    found = config.find_without_child(
        r"^interface ",
        [r"^ip address ", r"^shutdown"],
    )
    assert found == []


def test_find_without_child_pattern_optional() -> None:
    """A ``None`` target matches any node lacking the given child."""
    config = parse(SAMPLE)
    found = config.find_without_child(None, r"^ip address ")
    texts = [n.text for n in found]
    # The node carrying ``ip address`` (interface Gi0/0) is excluded; everything
    # else in the tree - including leaf lines - qualifies.
    assert "interface GigabitEthernet0/0" not in texts
    assert "interface GigabitEthernet0/1" in texts


def test_find_without_descendant_searches_any_depth() -> None:
    """``find_without_descendant`` excludes nodes with a deep match."""
    config = parse(SAMPLE)
    found = config.find_without_descendant(r"^router bgp ", r"activate")
    # ``router bgp`` has ``activate`` lines nested two levels down, so it is
    # excluded even though it has no direct child matching ``activate``.
    assert found == []
    # A child-only check would wrongly keep it: no direct child says ``activate``.
    by_child = config.find_without_child(r"^router bgp ", r"activate")
    assert [n.text for n in by_child] == ["router bgp 65000"]


def test_find_without_descendant_list_is_nor() -> None:
    """A node with any listed descendant below it is excluded (NOR)."""
    config = parse(SAMPLE)
    # ``router bgp`` contains ``activate`` (and ``vpnv4``) below it, so it is
    # excluded; the access-list, lacking both, qualifies.
    found = config.find_without_descendant(
        r"^router bgp |^ip access-list ",
        [r"activate", r"vpnv4"],
    )
    assert [n.text for n in found] == ["ip access-list extended PERMIT_WEB"]


def test_find_without_parent_single() -> None:
    """``find_without_parent`` excludes nodes under a matching parent."""
    config = parse(SAMPLE)
    found = config.find_without_parent(r"activate", r"address-family ipv4")
    # Only the vpnv4 neighbor remains; the two ipv4 neighbors are excluded.
    assert [n.text for n in found] == ["neighbor 10.0.0.1 activate"]


def test_find_without_parent_includes_top_level() -> None:
    """A parentless (top-level) node qualifies for ``find_without_parent``."""
    config = parse(SAMPLE)
    found = config.find_without_parent(r"^interface ", r"^router bgp ")
    # Both interfaces are top-level, so they have no parent at all and qualify.
    assert [n.text for n in found] == [
        "interface GigabitEthernet0/0",
        "interface GigabitEthernet0/1",
    ]


def test_find_without_parent_list_is_nor() -> None:
    """A parent matching any listed pattern excludes the node (NOR)."""
    config = parse(SAMPLE)
    # The ipv4 neighbors' parent matches ``ipv4`` (one of the two patterns), so
    # they are excluded even though it does not match ``vpnv4``.
    found = config.find_without_parent(
        r"activate",
        [r"address-family ipv4", r"address-family vpnv4"],
    )
    assert found == []


def test_find_without_ancestor_single_spans_all_depths() -> None:
    """A single ancestor pattern excludes matches at any depth below it."""
    config = parse(SAMPLE)
    found = config.find_without_ancestor(r"activate", r"router bgp")
    # Every ``activate`` line sits under ``router bgp`` somewhere above, so none
    # qualify.
    assert found == []


def test_find_without_ancestor_includes_top_level() -> None:
    """A top-level node has no ancestors and always qualifies."""
    config = parse(SAMPLE)
    found = config.find_without_ancestor(r"^interface ", r"^router bgp ")
    assert [n.text for n in found] == [
        "interface GigabitEthernet0/0",
        "interface GigabitEthernet0/1",
    ]


def test_find_without_ancestor_list_is_nor() -> None:
    """Any listed ancestor anywhere above excludes the node (NOR)."""
    config = parse(SAMPLE)
    # ``router bgp`` is a grandparent of the ipv4 neighbors, matching one of the
    # two patterns, so they are excluded under NOR.
    found = config.find_without_ancestor(
        r"activate",
        [r"router bgp", r"some-other-context"],
    )
    assert found == []


def test_find_without_ancestor_partial_match_excluded() -> None:
    """Having one of several ancestors present still excludes a node (NOR)."""
    config = parse(SAMPLE)
    # The deny/permit lines sit under ``ip access-list`` but not under any
    # ``interface``; because one listed ancestor is present they are excluded.
    found = config.find_without_ancestor(
        r"^permit |^deny ",
        [r"^ip access-list ", r"^interface "],
    )
    assert found == []


def test_helpers_scope_to_a_subtree() -> None:
    """The negative helpers work on any node, scoping to its subtree."""
    config = parse(SAMPLE)
    bgp = config.find_one(r"^router bgp ")
    assert bgp is not None
    found = bgp.find_without_parent(r"activate", r"address-family vpnv4")
    assert [n.text for n in found] == [
        "neighbor 10.0.0.1 activate",
        "neighbor 10.0.0.2 activate",
    ]
