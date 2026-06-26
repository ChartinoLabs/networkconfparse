"""Small shared helpers with no dependency on the node tree."""

from __future__ import annotations

import re

from .typedefs import Patterns


def _as_list(value: Patterns) -> list[str | re.Pattern[str]]:
    """Normalise a single pattern or an iterable of patterns into a list."""
    if isinstance(value, (str, re.Pattern)):
        return [value]
    return list(value)
