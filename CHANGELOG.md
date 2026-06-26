# Changelog

All notable changes to networkconfparse are documented in this file.

<!-- towncrier release notes start -->

## 0.1.0 - 2026-06-26

### Added

- Initial release of `networkconfparse`, a library for parsing the whitespace-indented configuration of network infrastructure (Cisco IOS, IOS XE, IOS XR, and NX-OS) into a queryable tree of parent/child `ConfigNode` objects.
- Network-OS-agnostic parser that infers hierarchy from relative indentation (no fixed indent width assumed), transparently skipping `!` comment and section-delimiter lines, and capturing multiline `banner` blocks and inline certificate data as verbatim bodies rather than mistaking them for configuration.
- A composable query API on both `Config` and `ConfigNode`: regex- and predicate-driven `find`, `find_one`, `find_child`, and `has_child`; relationship helpers `find_with_child`, `find_with_descendant`, `find_with_parent`, and `find_with_ancestor`; and node navigation via `ancestors`, `descendants`, `root`, and `path`.
