# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["AuthorListParams"]


class AuthorListParams(TypedDict, total=False):
    content_types: Annotated[str, PropertyInfo(alias="contentTypes")]

    last_active_date: Annotated[str, PropertyInfo(alias="lastActiveDate")]

    member_since_date: Annotated[str, PropertyInfo(alias="memberSinceDate")]

    page_number: Annotated[float, PropertyInfo(alias="pageNumber")]
    """Page number to fetch"""

    page_size: Annotated[float, PropertyInfo(alias="pageSize")]
    """Number of authors per page"""

    sort_by: Annotated[
        Literal[
            "trustLevel",
            "violationCount",
            "reportCount",
            "memberSince",
            "lastActive",
            "contentCount",
            "flaggedContentRatio",
            "averageSentiment",
        ],
        PropertyInfo(alias="sortBy"),
    ]

    sort_direction: Annotated[Literal["asc", "desc"], PropertyInfo(alias="sortDirection")]
    """Sort direction"""
