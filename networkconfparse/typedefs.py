"""Shared type aliases for the query API.

Kept free of runtime dependencies on the node tree: ``ConfigNode`` is imported
only for type checking and referenced via a forward reference, so ``node.py``
can import these aliases without creating an import cycle.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from .node import ConfigNode

# A single regex pattern, or an iterable of them (all combined with AND).
Patterns: TypeAlias = str | re.Pattern[str] | Iterable[str | re.Pattern[str]]

# A callable that tests a node and returns whether it matches.
Predicate: TypeAlias = Callable[["ConfigNode"], bool]
