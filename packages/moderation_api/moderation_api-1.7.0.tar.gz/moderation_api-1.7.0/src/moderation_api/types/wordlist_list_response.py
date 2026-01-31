# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import TypeAlias

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["WordlistListResponse", "WordlistListResponseItem"]


class WordlistListResponseItem(BaseModel):
    id: str
    """Unique identifier of the wordlist"""

    created_at: Optional[str] = FieldInfo(alias="createdAt", default=None)
    """When the wordlist was created"""

    description: Optional[str] = None
    """Description of the wordlist"""

    name: Optional[str] = None
    """Name of the wordlist"""

    user_id: Optional[str] = FieldInfo(alias="userId", default=None)
    """User who created the wordlist"""


WordlistListResponse: TypeAlias = List[WordlistListResponseItem]
