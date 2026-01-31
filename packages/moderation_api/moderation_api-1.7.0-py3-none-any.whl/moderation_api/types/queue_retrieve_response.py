# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["QueueRetrieveResponse", "Queue", "QueueFilter", "QueueFilterFilterLabel"]


class QueueFilterFilterLabel(BaseModel):
    label: str

    type: Literal["FLAGGED", "NOT_FLAGGED", "THRESHOLDS"]

    max_threshold: Optional[float] = FieldInfo(alias="maxThreshold", default=None)

    min_threshold: Optional[float] = FieldInfo(alias="minThreshold", default=None)


class QueueFilter(BaseModel):
    after_date: Optional[str] = FieldInfo(alias="afterDate", default=None)

    author_id: Optional[str] = FieldInfo(alias="authorID", default=None)

    before_date: Optional[str] = FieldInfo(alias="beforeDate", default=None)

    conversation_ids: Optional[List[Optional[str]]] = FieldInfo(alias="conversationIds", default=None)

    filtered_action_ids: Optional[List[str]] = FieldInfo(alias="filteredActionIds", default=None)

    filtered_channel_ids: Optional[List[str]] = FieldInfo(alias="filteredChannelIds", default=None)

    filter_labels: Optional[List[QueueFilterFilterLabel]] = FieldInfo(alias="filterLabels", default=None)

    labels: Optional[List[str]] = None

    recommendation_actions: Optional[List[Literal["review", "allow", "reject"]]] = FieldInfo(
        alias="recommendationActions", default=None
    )

    show_checked: Optional[bool] = FieldInfo(alias="showChecked", default=None)


class Queue(BaseModel):
    id: str

    description: str

    filter: QueueFilter

    name: str

    resolved_items_count: float = FieldInfo(alias="resolvedItemsCount")

    total_items_count: float = FieldInfo(alias="totalItemsCount")

    unresolved_items_count: float = FieldInfo(alias="unresolvedItemsCount")


class QueueRetrieveResponse(BaseModel):
    queue: Queue
