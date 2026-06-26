"""Tests for inline certificate (hex) data parsing."""

from networkconfparse import parse

SAMPLE = (
    "crypto pki trustpoint TP-self-signed-1597520745\n"
    " enrollment selfsigned\n"
    " revocation-check none\n"
    "crypto pki certificate chain TP-self-signed-1597520745\n"
    " certificate self-signed 01\n"
    "  30820330 30820218 A0030201 02020101 300D0609 2A864886 F70D0101 0D050030\n"
    "  31312F30 2D060355 04030C26 494F532D 53656C66 2D536967 6E65642D 43657274\n"
    "        quit\n"
    "crypto pki certificate chain SLA-TrustPoint\n"
    " certificate ca 01\n"
    "  30820321 30820209 A0030201 02020101 300D0609 2A864886 F70D0101 0B050030\n"
    "        quit\n"
)


def test_certificate_body_does_not_pollute_top_level() -> None:
    """Hex body lines never become top-level (or stray) configuration nodes."""
    config = parse(SAMPLE)
    assert [n.text for n in config] == [
        "crypto pki trustpoint TP-self-signed-1597520745",
        "crypto pki certificate chain TP-self-signed-1597520745",
        "crypto pki certificate chain SLA-TrustPoint",
    ]


def test_surrounding_config_parses_normally() -> None:
    """Trustpoint blocks around the certificate data are unaffected."""
    config = parse(SAMPLE)
    trustpoint = config.nodes[0]
    assert [c.text for c in trustpoint.children] == [
        "enrollment selfsigned",
        "revocation-check none",
    ]


def test_hex_body_attaches_to_the_certificate_node() -> None:
    """Hex lines become verbatim children of the certificate line."""
    config = parse(SAMPLE)
    chain = config.nodes[1]
    certificate = chain.children[0]
    assert certificate.text == "certificate self-signed 01"
    assert [c.text for c in certificate.children] == [
        "  30820330 30820218 A0030201 02020101 300D0609 2A864886 F70D0101 0D050030",
        "  31312F30 2D060355 04030C26 494F532D 53656C66 2D536967 6E65642D 43657274",
    ]


def test_quit_terminator_is_dropped() -> None:
    """The ``quit`` terminator is not retained anywhere in the tree."""
    config = parse(SAMPLE)
    assert config.find(r"^quit$") == []


def test_multiple_certificate_chains_are_siblings() -> None:
    """Each certificate chain parses as its own top-level node."""
    config = parse(SAMPLE)
    chains = config.find(r"^crypto pki certificate chain ")
    assert len(chains) == 2
    assert [c.children[0].text for c in chains] == [
        "certificate self-signed 01",
        "certificate ca 01",
    ]


def test_certificate_without_chain_context_is_not_consumed() -> None:
    """A ``certificate`` line outside a chain is parsed normally, not consumed.

    Without the context guard, consumption would run to end-of-input looking for
    a ``quit`` that never comes, swallowing later configuration.
    """
    cfg = "certificate foo\n some child\nhostname r1\n"
    config = parse(cfg)
    assert [n.text for n in config] == ["certificate foo", "hostname r1"]
    assert [c.text for c in config.nodes[0].children] == ["some child"]
