# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo

__all__ = ["ExecuteExecuteByIDParams"]


class ExecuteExecuteByIDParams(TypedDict, total=False):
    author_ids: Annotated[SequenceNotStr[str], PropertyInfo(alias="authorIds")]
    """IDs of the authors to apply the action to"""

    content_ids: Annotated[SequenceNotStr[str], PropertyInfo(alias="contentIds")]
    """The IDs of the content items to perform the action on."""

    queue_id: Annotated[str, PropertyInfo(alias="queueId")]
    """The ID of the queue the action was performed from if any."""

    value: str
    """The value of the action. Useful to set a reason for the action etc."""
