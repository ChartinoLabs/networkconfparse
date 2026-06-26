"""Tests for the navigation and query primitives."""

from networkconfparse import parse

SAMPLE = """\
interface GigabitEthernet0/0
 ip address 10.0.0.1 255.255.255.0
 no shutdown
interface GigabitEthernet0/1
 no ip address
 shutdown
interface Loopback0
 ip address 1.1.1.1 255.255.255.255
ip access-list extended PERMIT_WEB
 permit tcp any any eq 80
 deny ip any any
ip access-list extended NO_TRAILING_DENY
 permit tcp any any eq 22
"""


def test_matches_uses_regex_search() -> None:
    """``matches`` searches anywhere in the line unless anchored."""
    config = parse("interface GigabitEthernet0/0\n")
    intf = config.nodes[0]
    assert intf.matches("interface")
    assert intf.matches(r"^interface Gig")
    assert not intf.matches(r"^ip address")


def test_walk_is_depth_first() -> None:
    """``walk`` yields every node in pre-order across the configuration."""
    config = parse("a\n b\n  c\n d\n")
    assert [n.text for n in config.walk()] == ["a", "b", "c", "d"]


def test_find_searches_whole_subtree() -> None:
    """``find`` returns matching nodes at any depth."""
    config = parse(SAMPLE)
    addresses = config.find(r"^ip address ")
    assert [n.text for n in addresses] == [
        "ip address 10.0.0.1 255.255.255.0",
        "ip address 1.1.1.1 255.255.255.255",
    ]


def test_find_child_only_direct_children() -> None:
    """``find_child`` considers immediate children only and returns the first."""
    config = parse(SAMPLE)
    intf = config.find_child(r"^interface GigabitEthernet0/0")
    assert intf is not None
    no_shutdown = intf.find_child(r"^no shutdown")
    assert no_shutdown is not None
    assert no_shutdown.text == "no shutdown"
    # The IP address lives one level deeper, so it is not a top-level line.
    assert config.find_child(r"^ip address ") is None


def test_has_child_predicate() -> None:
    """``has_child`` reports whether any immediate child matches."""
    config = parse(SAMPLE)
    intf = config.find_child(r"^interface GigabitEthernet0/0")
    assert intf is not None
    assert intf.has_child(r"^ip address ")
    assert not intf.has_child(r"^description ")


def test_query_interfaces_with_ip_address() -> None:
    """End-to-end: find all interfaces that have an IP address configured."""
    config = parse(SAMPLE)
    interfaces = config.find(r"^interface ")
    with_ip = [i.text for i in interfaces if i.has_child(r"^ip address ")]
    assert with_ip == [
        "interface GigabitEthernet0/0",
        "interface Loopback0",
    ]


def test_query_acls_without_trailing_deny() -> None:
    """End-to-end: find ACLs that do not end with an explicit deny."""
    config = parse(SAMPLE)
    acls = config.find(r"^ip access-list ")
    without_trailing_deny = [
        acl.text
        for acl in acls
        if not acl.children or not acl.children[-1].matches(r"^deny ")
    ]
    assert without_trailing_deny == ["ip access-list extended NO_TRAILING_DENY"]
