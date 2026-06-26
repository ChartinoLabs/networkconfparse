"""Tests for the navigation and query primitives on ConfigNode."""

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
    root = parse("interface GigabitEthernet0/0\n")
    intf = root.children[0]
    assert intf.matches("interface")
    assert intf.matches(r"^interface Gig")
    assert not intf.matches(r"^ip address")


def test_walk_is_depth_first() -> None:
    """``walk`` yields every descendant in pre-order, excluding self."""
    root = parse("a\n b\n  c\n d\n")
    assert [n.text for n in root.walk()] == ["a", "b", "c", "d"]


def test_find_searches_whole_subtree() -> None:
    """``find`` returns matching descendants at any depth."""
    root = parse(SAMPLE)
    addresses = root.find(r"^ip address ")
    assert [n.text for n in addresses] == [
        "ip address 10.0.0.1 255.255.255.0",
        "ip address 1.1.1.1 255.255.255.255",
    ]


def test_find_child_only_direct_children() -> None:
    """``find_child`` considers direct children only and returns the first."""
    root = parse(SAMPLE)
    intf = root.find_child(r"^interface GigabitEthernet0/0")
    assert intf is not None
    no_shutdown = intf.find_child(r"^no shutdown")
    assert no_shutdown is not None
    assert no_shutdown.text == "no shutdown"
    # The IP address lives one level deeper, so it is not a direct child of root.
    assert root.find_child(r"^ip address ") is None


def test_has_child_predicate() -> None:
    """``has_child`` reports whether any direct child matches."""
    root = parse(SAMPLE)
    intf = root.find_child(r"^interface GigabitEthernet0/0")
    assert intf is not None
    assert intf.has_child(r"^ip address ")
    assert not intf.has_child(r"^description ")


def test_query_interfaces_with_ip_address() -> None:
    """End-to-end: find all interfaces that have an IP address configured."""
    root = parse(SAMPLE)
    interfaces = root.find(r"^interface ")
    with_ip = [i.text for i in interfaces if i.has_child(r"^ip address ")]
    assert with_ip == [
        "interface GigabitEthernet0/0",
        "interface Loopback0",
    ]


def test_query_acls_without_trailing_deny() -> None:
    """End-to-end: find ACLs that do not end with an explicit deny."""
    root = parse(SAMPLE)
    acls = root.find(r"^ip access-list ")
    without_trailing_deny = [
        acl.text
        for acl in acls
        if not acl.children or not acl.children[-1].matches(r"^deny ")
    ]
    assert without_trailing_deny == ["ip access-list extended NO_TRAILING_DENY"]
