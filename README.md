# networkconfparse

[![CI](https://github.com/ChartinoLabs/networkconfparse/actions/workflows/ci.yml/badge.svg)](https://github.com/ChartinoLabs/networkconfparse/actions/workflows/ci.yml)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![PyPI version](https://img.shields.io/pypi/v/networkconfparse)](https://pypi.org/project/networkconfparse/)
[![PyPI downloads](https://img.shields.io/pypi/dm/networkconfparse)](https://pypi.org/project/networkconfparse/)
[![Python versions](https://img.shields.io/pypi/pyversions/networkconfparse)](https://pypi.org/project/networkconfparse/)
[![License](https://img.shields.io/pypi/l/networkconfparse)](https://github.com/ChartinoLabs/networkconfparse/blob/main/LICENSE)

networkconfparse is a library that parses the whitespace-indented configuration of network infrastructure (Cisco IOS, IOS XE, IOS XR, and NX-OS) into a queryable tree of native Python objects.

## Why networkconfparse?

- **Standalone** - No runtime dependencies. Install and use it in any Python project.
- **Network-OS agnostic** - Hierarchy is inferred from relative indentation, so IOS (one space), NX-OS (two spaces), and inconsistent indentation are all handled without per-platform rules.
- **Queryable** - A small, composable API to find configuration objects by regex, by predicate, or by their parent/child relationships.
- **Handles the awkward parts** - Transparently skips `!` comment and delimiter lines and captures multiline `banner` blocks and inline certificate data as opaque bodies, rather than mistaking them for configuration.
- **Typed and well-tested** - Fully type-hinted with a comprehensive test suite.

## Installation

networkconfparse can be quickly and easily installed with `uv` as shown below:

```bash
uv add networkconfparse
```

Or, if you prefer good old-fashioned `pip`, you can do so as shown below:

```bash
pip install networkconfparse
```

## Quick Examples

### Parsing a Configuration

Call `parse()` with the configuration text. It returns a `Config` whose top-level lines each carry their indented children as a tree of `ConfigNode` objects. Comment/delimiter lines (`!`) are dropped automatically.

```python
import networkconfparse

config = networkconfparse.parse("""
interface GigabitEthernet0/0
 ip address 10.0.0.1 255.255.255.0
 no shutdown
!
interface GigabitEthernet0/1
 shutdown
!
""")

for interface in config.find(r"^interface "):
    print(interface.text, "->", [child.text for child in interface.children])
```

Prints:

```text
interface GigabitEthernet0/0 -> ['ip address 10.0.0.1 255.255.255.0', 'no shutdown']
interface GigabitEthernet0/1 -> ['shutdown']
```

### Querying the Tree

`find()` searches the entire tree and accepts a regular expression, a `where` predicate, or both. `find_child()`/`has_child()` look only at a node's immediate children, and `find_one()` returns the first match. Every node also exposes `path`, `ancestors`, `descendants`, and `root` for navigation.

```python
# Interfaces that have an IP address configured anywhere beneath them.
configured = config.find(r"^interface ", where=lambda node: node.has_child(r"^ip address "))

# The first matching line, or None.
mgmt = config.find_one(r"^ip address 10\.0\.0\.1")

# Where does that line live in the hierarchy?
print(mgmt.path)
# ['interface GigabitEthernet0/0', 'ip address 10.0.0.1 255.255.255.0']
```

### Relationship Helpers

For the common cases, dedicated helpers read more clearly than a hand-written predicate. Each accepts a single regex or a list (combined with AND), and they are simply convenience wrappers around `find()`:

```python
# Parents matching "interface" that have BOTH children as direct children.
config.find_with_child(r"^interface ", [r"^ip address ", r"^no shutdown"])

# Parents that have a matching line anywhere below them (not just direct children).
config.find_with_descendant(r"^router bgp ", r"neighbor")

# Lines whose direct parent matches.
config.find_with_parent(r"^neighbor ", r"^address-family ipv4")

# Lines with a matching ancestor anywhere above (or a consecutive chain with adjacent=True).
config.find_with_ancestor(r"^neighbor ", [r"^router bgp ", r"^address-family ipv4"])
```

These compose naturally for SDK-style questions. For example, "find every ACL that does not end with an explicit deny":

```python
acls = config.find(r"^ip access-list ")
missing_deny = [
    acl for acl in acls
    if not acl.children or not acl.children[-1].matches(r"^deny ")
]
```

## Documentation

- [Changelog](CHANGELOG.md) - Release history built from changelog fragments
- [Changelog Fragments Guide](changes/README.md) - How to add release-note fragments

## Acknowledgments

- **Conceptual inspiration** - The idea of modeling a network device configuration as a queryable parent/child tree owes a great deal to [Mike Pennington](https://github.com/mpenning)'s work on [CiscoConfParse](https://github.com/mpenning/ciscoconfparse) and [CiscoConfParse2](https://github.com/mpenning/ciscoconfparse2). networkconfparse is an independent, clean-room implementation; it is not affiliated with, derived from, or endorsed by those projects.

## Status

Early development. The API is still evolving and may change as the library matures.
