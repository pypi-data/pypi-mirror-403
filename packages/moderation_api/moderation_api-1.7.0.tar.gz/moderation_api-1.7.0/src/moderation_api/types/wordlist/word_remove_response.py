# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["WordRemoveResponse"]


class WordRemoveResponse(BaseModel):
    removed_count: float = FieldInfo(alias="removedCount")
    """Number of words removed"""

    removed_words: List[str] = FieldInfo(alias="removedWords")
    """List of words removed"""

    total_count: float = FieldInfo(alias="totalCount")
    """Total number of words in wordlist"""
