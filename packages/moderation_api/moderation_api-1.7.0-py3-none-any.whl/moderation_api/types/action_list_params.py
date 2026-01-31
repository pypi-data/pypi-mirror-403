# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["ActionListParams"]


class ActionListParams(TypedDict, total=False):
    queue_id: Annotated[str, PropertyInfo(alias="queueId")]
