# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["QueueGetStatsParams"]


class QueueGetStatsParams(TypedDict, total=False):
    within_days: Annotated[str, PropertyInfo(alias="withinDays")]
    """Number of days to analyze statistics for"""
