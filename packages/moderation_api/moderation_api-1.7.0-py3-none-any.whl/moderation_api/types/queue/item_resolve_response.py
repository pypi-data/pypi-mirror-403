# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["ItemResolveResponse"]


class ItemResolveResponse(BaseModel):
    resolved_at: str = FieldInfo(alias="resolvedAt")
    """Timestamp when the item was resolved"""

    success: bool

    comment: Optional[str] = None
    """Optional comment"""
