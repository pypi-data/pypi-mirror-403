# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["WordAddResponse"]


class WordAddResponse(BaseModel):
    added_count: float = FieldInfo(alias="addedCount")
    """Number of words added"""

    added_words: List[str] = FieldInfo(alias="addedWords")
    """List of words that were added"""

    total_count: float = FieldInfo(alias="totalCount")
    """Total number of words in wordlist"""
