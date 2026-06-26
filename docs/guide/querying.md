# Querying

Every query method is available on both [`Config`](../reference/config.md) (where
it searches the whole configuration) and any individual
[`ConfigNode`](../reference/node.md) (where it searches that node's subtree). This
page covers the full API; the examples assume a parsed `config`.

## Matching: regex or predicate

`find()` is the workhorse. It accepts an optional regular expression `pattern`, an
optional `where` predicate, or both (combined with **AND**):

```python
# By regex (re.search semantics — anchor with ^ when you mean it).
config.find(r"^interface ")

# By predicate.
config.find(where=lambda node: not node.children)        # leaf lines

# Both: must satisfy the regex AND the predicate.
config.find(r"^interface ", where=lambda node: node.has_child(r"^ip address "))

# Neither: every node in the subtree.
config.find()
```

!!! note
    Matching uses `re.search`, so a pattern matches anywhere in the line unless
    you anchor it. `r"^ip address "` deliberately excludes `no ip address`.

`find_one()` returns the first match in document order, or `None`:

```python
first_ip = config.find_one(r"^ip address ")
```

## Direct children only

`find_child()` and `has_child()` consider only a node's **immediate** children,
not its whole subtree:

```python
interface = config.find_one(r"^interface GigabitEthernet0/0")
interface.has_child(r"^ip address ")            # True
interface.find_child(r"^shutdown")              # the child node, or None
```

## Relationship helpers

These wrap `find()` with a `where` predicate for the most common questions. Each
accepts a single regex **or a list** of them (combined with AND).

| Helper | Returns nodes matching `pattern` that… |
|--------|-----------------------------------------|
| `find_with_child(pattern, child)` | have all of `child` as **direct** children |
| `find_with_descendant(pattern, descendant)` | have all of `descendant` **anywhere below** |
| `find_with_parent(pattern, parent)` | whose **direct parent** matches `parent` |
| `find_with_ancestor(pattern, ancestor)` | have `ancestor` **anywhere above** |

```python
# Interfaces that have both lines as direct children.
config.find_with_child(r"^interface ", [r"^ip address ", r"^no shutdown"])

# Router processes that mention a neighbor anywhere beneath them.
config.find_with_descendant(r"^router bgp ", r"neighbor")

# Neighbor lines directly under an IPv4 address-family.
config.find_with_parent(r"activate", r"^address-family ipv4")
```

`find_with_ancestor` defaults to matching each ancestor pattern **anywhere** above
the node, in any order. Pass `adjacent=True` to require a consecutive chain,
matched nearest-first (the first pattern against the direct parent, the next
against its parent, and so on):

```python
# `activate` somewhere under both a BGP process and an IPv4 address-family.
config.find_with_ancestor(r"activate", [r"^router bgp ", r"^address-family ipv4"])

# `activate` whose direct parent is the address-family, whose parent is the BGP process.
config.find_with_ancestor(
    r"activate",
    [r"^address-family ipv4", r"^router bgp "],
    adjacent=True,
)
```

## Navigating the tree

Beyond searching, each node knows its place in the hierarchy:

- `path` - the list of ancestor texts from the top-most line down to this one.
- `ancestors` - iterate upward, nearest parent first.
- `descendants` - iterate the whole subtree, depth-first (equivalent to `walk()`).
- `root` - the top-level line this node belongs to.

```python
addr = config.find_one(r"^ip address ")
addr.path             # ['interface GigabitEthernet0/0', 'ip address 10.0.0.1 255.255.255.0']
addr.root.text        # 'interface GigabitEthernet0/0'
```

## Worked example: ACLs without a trailing deny

The helpers and navigation compose into SDK-style questions. For example, "find
every ACL that does not end with an explicit deny":

```python
acls = config.find(r"^ip access-list ")
missing_deny = [
    acl for acl in acls
    if not acl.children or not acl.children[-1].matches(r"^deny ")
]
```
