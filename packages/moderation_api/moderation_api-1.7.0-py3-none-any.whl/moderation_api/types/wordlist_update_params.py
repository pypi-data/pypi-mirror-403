# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

from .._types import SequenceNotStr

__all__ = ["WordlistUpdateParams"]


class WordlistUpdateParams(TypedDict, total=False):
    description: str
    """New description for the wordlist"""

    key: str
    """New key for the wordlist"""

    name: str
    """New name for the wordlist"""

    strict: bool
    """Deprecated. Now using threshold in project settings."""

    words: SequenceNotStr[str]
    """New words for the wordlist.

    Replace the existing words with these new ones. Duplicate words will be ignored.
    """
