# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["ItemUnresolveResponse"]


class ItemUnresolveResponse(BaseModel):
    status: str
    """New status of the item"""

    success: bool

    unresolved_at: str = FieldInfo(alias="unresolvedAt")
    """Timestamp when the item was unresolved"""
