# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["ExecuteExecuteByIDResponse"]


class ExecuteExecuteByIDResponse(BaseModel):
    action_id: str = FieldInfo(alias="actionId")
    """The ID of the action."""

    ids: List[str]
    """The IDs of the content items."""

    success: bool
    """Action executed successfully."""
