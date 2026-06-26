# Parsing Model

Understanding how networkconfparse turns text into a tree makes the query API
predictable. This page describes that model.

## Lines become a tree

[`parse`](../reference/parse.md) reads the configuration line by line and builds a
tree of [`ConfigNode`](../reference/node.md) objects. A line is a **child** of the
nearest preceding line with *strictly less* indentation. The top-level (column 0)
lines become the children of the returned [`Config`](../reference/config.md).

```text
interface GigabitEthernet0/0          <- top-level node
 ip address 10.0.0.1 255.255.255.0    <- child of the interface
 no shutdown                          <- child of the interface
```

Each node stores its stripped `text`, its `parent`, and its `children`.

## Indentation is relative, not fixed

The parser makes **no assumption about indent width**. It compares the leading
whitespace of each line to the lines above it, so a single-space IOS style, a
two-space NX-OS style, and even inconsistent indentation all produce the same
shape. Tabs are expanded before measuring. A dedent simply re-attaches the
following line to the correct ancestor.

## Comment and delimiter lines are dropped

Lines whose first non-whitespace character is `!` are comments or section
delimiters in Cisco platforms. They carry no configuration semantics and are
**skipped during parsing** - they never become nodes. This is safe because the
tree's shape is determined entirely by indentation; a `!` delimiter is redundant
with the dedent that already closes a block.

A `!` that appears *within* a line (for example `description has!bang`) is part of
the text and is preserved.

## Banners and certificates are captured as bodies

Some configuration contains freeform, multi-line payloads whose lines are not
indentation-structured and may even look like configuration. The parser
recognizes these and captures their body verbatim as children of the owning line,
rather than mistaking the body for real configuration:

- **`banner` blocks** - `banner motd ^C` followed by body text until the
  delimiter character reappears. The body (which may contain `!`, blank lines, or
  config-looking text) is attached to the banner node; the closing delimiter is
  dropped.
- **Inline certificate data** - a `certificate ...` line inside a
  `crypto pki certificate chain` block, whose hex body runs until a standalone
  `quit`. The hex is attached to the certificate node; `quit` is dropped.

Because these bodies are captured as a unit, they never pollute the rest of the
tree, and queries over the surrounding configuration behave exactly as expected.
