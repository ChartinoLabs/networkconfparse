# Quick Start

## Parse a configuration

Call [`parse`](../reference/parse.md) with the configuration text. It returns a
[`Config`](../reference/config.md) whose top-level lines each carry their indented
children as a tree of [`ConfigNode`](../reference/node.md) objects. Comment and
delimiter lines (`!`) are dropped automatically.

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

```text
interface GigabitEthernet0/0 -> ['ip address 10.0.0.1 255.255.255.0', 'no shutdown']
interface GigabitEthernet0/1 -> ['shutdown']
```

## Parse from a file, path, or lines

`parse()` is the single entry point for every common starting point, not just a
text string. It dispatches on the type of its argument:

| Input                                      | Interpretation                          |
| ------------------------------------------ | --------------------------------------- |
| `str` containing a newline                 | literal configuration text              |
| `str` without a newline                    | tasted as a path, else literal text     |
| `pathlib.Path`                             | always a filesystem path                |
| file-like object (has `.read()`)           | its contents are read                   |
| iterable of `str` (list/tuple/generator)   | joined as lines                         |

```python
from pathlib import Path

import networkconfparse

# An explicit Path always reads the file (and raises if it is missing).
config = networkconfparse.parse(Path("/etc/configs/router1.cfg"))

# An open file object is read directly.
with open("/etc/configs/router1.cfg") as handle:
    config = networkconfparse.parse(handle)

# An already-split list of lines is joined and parsed.
config = networkconfparse.parse(["interface GigabitEthernet0/0", " shutdown"])

# A bare string is "tasted": if it names an existing file it is read,
# otherwise it is parsed as configuration text.
config = networkconfparse.parse("router1.cfg")
```

A bare string containing a newline can never be a path, so it is always parsed
as text. The rare footgun is a single-line config that happens to match an
existing filename: it will be read as that file. To force literal-text
interpretation, append a trailing newline. See the [`parse`
reference](../reference/parse.md) for the full string-tasting rule.

## Run a query

`find()` searches the whole tree and accepts a regular expression, a `where`
predicate, or both:

```python
# Interfaces that have an IP address configured anywhere beneath them.
configured = config.find(r"^interface ", where=lambda node: node.has_child(r"^ip address "))

# The first matching line, or None.
mgmt = config.find_one(r"^ip address 10\.0\.0\.1")

# Where does that line live in the hierarchy?
print(mgmt.path)
# ['interface GigabitEthernet0/0', 'ip address 10.0.0.1 255.255.255.0']
```

## Use a relationship helper

For common cases, dedicated helpers read more clearly than a hand-written
predicate. The query above is identical to:

```python
configured = config.find_with_child(r"^interface ", r"^ip address ")
```

Continue to the [Querying guide](../guide/querying.md) for the full API.
