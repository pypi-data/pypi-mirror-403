# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["ItemListParams"]


class ItemListParams(TypedDict, total=False):
    after_date: Annotated[str, PropertyInfo(alias="afterDate")]

    author_id: Annotated[str, PropertyInfo(alias="authorId")]

    before_date: Annotated[str, PropertyInfo(alias="beforeDate")]

    conversation_ids: Annotated[str, PropertyInfo(alias="conversationIds")]

    filtered_action_ids: Annotated[str, PropertyInfo(alias="filteredActionIds")]

    include_resolved: Annotated[str, PropertyInfo(alias="includeResolved")]

    labels: str

    page_number: Annotated[float, PropertyInfo(alias="pageNumber")]
    """Page number to fetch"""

    page_size: Annotated[float, PropertyInfo(alias="pageSize")]
    """Number of items per page"""

    sort_direction: Annotated[Literal["asc", "desc"], PropertyInfo(alias="sortDirection")]
    """Sort direction"""

    sort_field: Annotated[Literal["createdAt", "severity", "reviewedAt"], PropertyInfo(alias="sortField")]
