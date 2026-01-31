# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["WordlistUpdateResponse"]


class WordlistUpdateResponse(BaseModel):
    id: str
    """ID of the wordlist"""

    created_at: str = FieldInfo(alias="createdAt")
    """Creation date of the wordlist"""

    name: Optional[str] = None
    """Name of the wordlist"""

    organization_id: str = FieldInfo(alias="organizationId")
    """ID of the organization"""

    strict: bool
    """Strict mode"""

    user_id: Optional[str] = FieldInfo(alias="userId", default=None)
    """ID of the user"""

    words: List[str]
    """Words in the wordlist"""
