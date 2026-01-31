# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["ItemListResponse", "Item", "ItemLabel", "ItemAction", "Pagination"]


class ItemLabel(BaseModel):
    flagged: bool
    """Whether this label caused a flag"""

    label: str
    """Label name"""

    score: float
    """Confidence score of the label"""


class ItemAction(BaseModel):
    id: str
    """Action ID"""

    name: str
    """Action name"""

    timestamp: float
    """Unix timestamp of when the action was taken"""

    comment: Optional[str] = None
    """Action comment"""

    reviewer: Optional[str] = None
    """Moderator userID"""


class Item(BaseModel):
    id: str
    """Content ID"""

    content: str
    """The content to be moderated"""

    flagged: bool
    """Whether the item is flagged by any label"""

    labels: List[ItemLabel]

    status: Literal["pending", "resolved"]
    """Status of the item"""

    timestamp: float
    """Unix timestamp of when the item was created"""

    actions: Optional[List[ItemAction]] = None
    """Action IDs taken on this item"""

    author_id: Optional[str] = FieldInfo(alias="authorId", default=None)
    """Author ID"""

    content_type: Optional[str] = FieldInfo(alias="contentType", default=None)
    """Type of the content object"""

    conversation_id: Optional[str] = FieldInfo(alias="conversationId", default=None)
    """Conversation ID"""

    language: Optional[str] = None
    """Content language"""


class Pagination(BaseModel):
    current_page: float = FieldInfo(alias="currentPage")

    has_next_page: bool = FieldInfo(alias="hasNextPage")

    has_previous_page: bool = FieldInfo(alias="hasPreviousPage")

    total_items: float = FieldInfo(alias="totalItems")

    total_pages: float = FieldInfo(alias="totalPages")


class ItemListResponse(BaseModel):
    items: List[Item]

    pagination: Pagination
