# Changelog

All notable changes to networkconfparse are documented in this file.

<!-- towncrier release notes start -->

## 0.2.0 - 2026-06-27

### Added

- Added negative relationship helpers `find_without_child`, `find_without_descendant`, `find_without_parent`, and `find_without_ancestor`, the discoverable counterparts to the `find_with_*` helpers for the common "matching lines that lack a given relationship" query. Given a list of patterns they apply a "none present" (NOR) rule, and top-level lines always qualify as having no parent or ancestor. ([#2](https://github.com/ChartinoLabs/networkconfparse/pull/2))
- Add a documentation site (MkDocs + Material) covering installation, the parsing model, and a usage guide, with an API reference auto-generated from docstrings via mkdocstrings, published to GitHub Pages.

### Changed

- `parse()` now accepts a filesystem path (`str` or `pathlib.Path`), an open file-like object, or an iterable of lines in addition to a configuration string, dispatching on the input so callers no longer have to read and join their config into one string first. ([#1](https://github.com/ChartinoLabs/networkconfparse/pull/1))

### Internal

- Add a documentation style guide and an enforcement test that fails CI if any Markdown file or `mkdocs.yml` contains em-dash or en-dash characters.


## 0.1.0 - 2026-06-26

### Added

- Initial release of `networkconfparse`, a library that parses the whitespace-indented configuration of network infrastructure (Cisco IOS, IOS XE, IOS XR, and NX-OS) into a queryable tree of parent/child `ConfigNode` objects. The indentation-based parser infers hierarchy without assuming a fixed indent width and captures `!` comment/delimiter lines, multiline `banner` blocks, and inline certificate data as opaque bodies; the query API provides regex- and predicate-driven `find`/`find_one`/`find_child`/`has_child`, relationship helpers (`find_with_child`, `find_with_descendant`, `find_with_parent`, `find_with_ancestor`), and node navigation (`ancestors`, `descendants`, `root`, `path`).

### Internal

- Add GitHub Actions CI and PyPI release pipelines, hatch-vcs dynamic versioning, and towncrier-managed changelog fragments.
