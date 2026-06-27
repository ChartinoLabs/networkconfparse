"""Generate the API reference pages and navigation by walking the package.

One Markdown page is emitted per public module under ``reference/`` and wired
into the navigation through a generated ``SUMMARY.md`` consumed by
mkdocs-literate-nav. New public modules and symbols therefore appear in the API
reference automatically, with no hand-maintained pages.
"""

from pathlib import Path

import mkdocs_gen_files

PACKAGE = "networkconfparse"

# Modules that are implementation details and must stay out of the public docs.
PRIVATE_MODULES = {"utils"}

# Friendly navigation labels and page titles, keyed by module name. Modules not
# listed fall back to their module name, so newly added modules still appear.
TITLES = {
    "parser": "parse",
    "config": "Config",
    "node": "ConfigNode",
    "typedefs": "Type Aliases",
}

# Navigation order, entry point first. Modules not listed sort alphabetically
# after these, so newly added modules still appear (just at the end).
ORDER = ["parser", "config", "node", "typedefs"]


def _sort_key(path: Path) -> tuple[int, str]:
    name = path.stem
    rank = ORDER.index(name) if name in ORDER else len(ORDER)
    return (rank, name)


root = Path(__file__).parent.parent
src = root / PACKAGE

nav = mkdocs_gen_files.Nav()

for path in sorted(src.rglob("*.py"), key=_sort_key):
    parts = path.relative_to(src).with_suffix("").parts
    name = parts[-1]
    if any(part.startswith("_") for part in parts) or name in PRIVATE_MODULES:
        # Skip dunder/private modules (__init__, _version) and internals.
        continue

    identifier = ".".join((PACKAGE, *parts))
    title = TITLES.get(name, name)
    heading = title if " " in title else f"`{title}`"
    doc_path = Path(*parts).with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    nav[(*parts[:-1], title)] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        # Suppress the module-level heading so a module that exposes a single
        # symbol renders as cleanly as a hand-written per-symbol page; the
        # module docstring still renders as the page intro.
        fd.write(f"# {heading}\n\n")
        fd.write(f"::: {identifier}\n")
        fd.write("    options:\n")
        fd.write("      show_root_heading: false\n")
        fd.write("      show_root_toc_entry: false\n")

    mkdocs_gen_files.set_edit_path(full_doc_path, path.relative_to(root))

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
