"""Internal utilities for daggr."""

from __future__ import annotations

import difflib


def suggest_similar(invalid: str, valid_options: set[str]) -> str | None:
    """Find a similar string from valid_options using fuzzy matching.

    Args:
        invalid: The invalid string to find matches for.
        valid_options: Set of valid options to search through.

    Returns:
        The closest matching string if found with >= 60% similarity, else None.
    """
    matches = difflib.get_close_matches(invalid, valid_options, n=1, cutoff=0.6)
    return matches[0] if matches else None
