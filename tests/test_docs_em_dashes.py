"""Documentation hygiene check: no em-dashes or en-dashes in documentation.

Em-dashes (U+2014) and en-dashes (U+2013) are visually similar to a hyphen but
are typed differently across operating systems and rarely render consistently in
plain-text editors, diffs, and code reviews. The project convention is to use a
plain ASCII hyphen with a single space on either side (` - `) instead.

This test scans every Markdown file in the repository and the top-level
``mkdocs.yml`` for these characters. Any occurrence fails the test with file
paths and line numbers to make remediation straightforward.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# Mapping of forbidden character to its human-readable name. Defined with escape
# sequences so this test file contains no literal em-dash or en-dash itself.
FORBIDDEN: dict[str, str] = {"\u2014": "em-dash", "\u2013": "en-dash"}
REPO_ROOT = Path(__file__).resolve().parent.parent
EXCLUDED_DIRS = frozenset({".venv", "site", ".git", "node_modules"})


def _iter_text_files() -> list[Path]:
    """Return every Markdown file in the repo plus mkdocs.yml, sorted."""
    files = [
        path for path in REPO_ROOT.rglob("*.md") if EXCLUDED_DIRS.isdisjoint(path.parts)
    ]
    mkdocs = REPO_ROOT / "mkdocs.yml"
    if mkdocs.is_file():
        files.append(mkdocs)
    return sorted(files)


def _find_forbidden(path: Path) -> list[tuple[int, str, str]]:
    """Return (line_number, character_name, line_text) for each offending line."""
    matches: list[tuple[int, str, str]] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        for character, name in FORBIDDEN.items():
            if character in line:
                matches.append((line_number, name, line.rstrip()))
    return matches


def test_no_unicode_dashes_in_documentation() -> None:
    """Fail if any Markdown file or mkdocs.yml contains an em-dash or en-dash.

    The project convention is a plain ASCII hyphen with a single space on either
    side (` - `). If this test fails, replace each character listed below.
    """
    offenders: dict[Path, list[tuple[int, str, str]]] = {}
    for path in _iter_text_files():
        matches = _find_forbidden(path)
        if matches:
            offenders[path] = matches

    if not offenders:
        return

    report = ["Unicode dash characters found in documentation:"]
    for path, matches in offenders.items():
        rel = path.relative_to(REPO_ROOT)
        for line_number, name, line_text in matches:
            report.append(f"  {rel}:{line_number}: ({name}) {line_text}")
    report.append("")
    report.append("Replace each with a plain ASCII hyphen ('-').")
    pytest.fail("\n".join(report))
