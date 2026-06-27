# networkconfparse

networkconfparse is a library that parses the whitespace-indented configuration of
network infrastructure (Cisco IOS, IOS XE, IOS XR, and NX-OS) into a queryable tree
of native Python objects.

## Why networkconfparse?

- **Standalone** - No runtime dependencies. Install and use it in any Python project.
- **Network-OS agnostic** - Hierarchy is inferred from relative indentation, so IOS (one space), NX-OS (two spaces), and inconsistent indentation are all handled without per-platform rules.
- **Queryable** - A small, composable API to find configuration objects by regex, by predicate, or by their parent/child relationships.
- **Handles the awkward parts** - Transparently skips `!` comment and delimiter lines and captures multiline `banner` blocks and inline certificate data as opaque bodies, rather than mistaking them for configuration.
- **Typed and well-tested** - Fully type-hinted with a comprehensive test suite.

## A taste

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

# Interfaces that have an IP address configured.
config.find_with_child(r"^interface ", r"^ip address ")
```

## Where to next

- [Installation](getting-started/installation.md) - add it to your project.
- [Quick Start](getting-started/quickstart.md) - parse a config and run your first queries.
- [Parsing Model](concepts/parsing-model.md) - how the tree is built, and how comments, banners, and certificates are handled.
- [Querying](guide/querying.md) - the full query API, in depth.
- [API Reference](reference/parser.md) - generated from the source.
