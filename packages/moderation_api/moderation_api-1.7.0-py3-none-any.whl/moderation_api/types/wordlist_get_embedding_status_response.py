# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["WordlistGetEmbeddingStatusResponse"]


class WordlistGetEmbeddingStatusResponse(BaseModel):
    """Embedding status details"""

    progress: float
    """Percentage of words that have been embedded (0-100)"""

    remaining_words: float = FieldInfo(alias="remainingWords")
    """Number of words still waiting to be embedded"""

    total_words: float = FieldInfo(alias="totalWords")
    """Total number of words in the wordlist"""
