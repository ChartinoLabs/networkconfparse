# Documentation Style Guide

This page defines the writing conventions for networkconfparse documentation.
Follow these rules when creating or editing pages under `docs/`, as well as the
top-level `README.md`, `RELEASING.md`, and changelog fragments.

## Structural rules

### Use headings for structural divisions, not bold text

If a piece of text introduces a distinct concept, variant, or category that a
reader might want to jump to, it must be a heading (`###`, `####`), not bold
inline text. Bold text is appropriate for emphasis within a sentence, but not as
a substitute for heading structure.

Headings appear in the table of contents, enable deep linking, and help readers
scan the page. Bold text does none of these.

### No numbered headings

Do not prefix headings with numbers to indicate sequence. Headings should
describe content, not position. If a procedure requires explicit ordering, use a
numbered list within a section rather than encoding the sequence into the heading
text.

### Heading hierarchy

Use heading levels to reflect the document outline. Do not skip levels (for
example, `##` followed by `####` with no `###` in between).

- `#` - page title (one per page)
- `##` - major sections
- `###` - subsections
- `####` - sub-subsections (use sparingly)

## Tables

### Pad table cells for alignment

Markdown table cells must be padded with spaces so that the column borders line
up vertically. This keeps tables readable in plain-text editors and diffs, not
just in rendered HTML.

Right:

```markdown
| Option      | Default    | Description        |
| ----------- | ---------- | ------------------ |
| `--pattern` | (required) | The regex to match. |
| `--first`   | off        | Return one result. |
```

## Punctuation and typography

### No em-dashes or en-dashes

Do not use the Unicode em-dash (U+2014) or en-dash (U+2013) characters, and do
not use double hyphens (`--`) as punctuation. Use a single space-surrounded
hyphen (` - `) instead, and a plain hyphen for ranges (for example, `3.11-3.13`).

These characters are visually similar to a hyphen but are typed differently
across operating systems and rarely render consistently in plain-text editors,
diffs, and code reviews. This rule is enforced by
`tests/test_docs_em_dashes.py`, which scans every Markdown file and `mkdocs.yml`.

### No smart quotes

Use straight quotes (`"`, `'`), not curly or smart quotes. Most editors default
to straight quotes; ensure yours does not auto-replace them.

## Prose style

### Lead with the outcome, not the mechanism

When describing what a feature does, state the user-visible outcome first, then
explain the mechanism if needed.

### Avoid LLM writing patterns

When using AI tools to draft documentation, watch for and correct these common
patterns:

- Bold-as-heading. If the bold text could have been a heading, make it one.
- Redundant lead-in sentences. Phrases like "Let's take a look at..." or "In this
  section, we will explore..." add no information. Start with the content.
- Over-qualification. Phrases like "It is important to note that" can almost
  always be deleted without changing the meaning.
- Trailing summaries. Restating what was just explained in an "In summary"
  paragraph. If the section is well-organized, the reader already understood it.

## Code examples

### Use fenced code blocks with language tags

Always specify the language for syntax highlighting (for example, ` ```python `
or ` ```bash `).

### Use realistic examples

Code examples should use plausible values: real command names, realistic IP
addresses, and device names that match the documentation context. Avoid
placeholder patterns like `foo`, `bar`, or `example-1`.

## Cross-references

Link to other documentation pages using relative paths, and include a short
description of what the linked page covers so the reader can decide whether to
follow the link.

Wrong: `See [here](reference/config.md).`

Right: `See the [Config reference](reference/config.md) for the full query API.`
