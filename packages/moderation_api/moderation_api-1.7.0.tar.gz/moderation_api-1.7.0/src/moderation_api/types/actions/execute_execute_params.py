# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo

__all__ = ["ExecuteExecuteParams"]


class ExecuteExecuteParams(TypedDict, total=False):
    action_key: Required[Annotated[str, PropertyInfo(alias="actionKey")]]
    """ID or key of the action to execute"""

    author_ids: Annotated[SequenceNotStr[str], PropertyInfo(alias="authorIds")]
    """IDs of the authors to apply the action to. Provide this or contentIds."""

    content_ids: Annotated[SequenceNotStr[str], PropertyInfo(alias="contentIds")]
    """IDs of the content items to apply the action to. Provide this or authorIds."""

    duration: float
    """Optional duration in milliseconds for actions with timeouts"""

    queue_id: Annotated[str, PropertyInfo(alias="queueId")]
    """Optional queue ID if the action is queue-specific"""

    value: str
    """Optional value to provide with the action"""
