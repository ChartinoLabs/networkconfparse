# Changelog

All notable changes to networkconfparse are documented in this file.

<!-- towncrier release notes start -->

## 0.1.0 - 2026-06-26

### Added

- Initial release of `networkconfparse`, a library that parses the whitespace-indented configuration of network infrastructure (Cisco IOS, IOS XE, IOS XR, and NX-OS) into a queryable tree of parent/child `ConfigNode` objects. The indentation-based parser infers hierarchy without assuming a fixed indent width and captures `!` comment/delimiter lines, multiline `banner` blocks, and inline certificate data as opaque bodies; the query API provides regex- and predicate-driven `find`/`find_one`/`find_child`/`has_child`, relationship helpers (`find_with_child`, `find_with_descendant`, `find_with_parent`, `find_with_ancestor`), and node navigation (`ancestors`, `descendants`, `root`, `path`).

### Internal

- Add GitHub Actions CI and PyPI release pipelines, hatch-vcs dynamic versioning, and towncrier-managed changelog fragments.
