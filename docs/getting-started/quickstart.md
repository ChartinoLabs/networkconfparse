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
