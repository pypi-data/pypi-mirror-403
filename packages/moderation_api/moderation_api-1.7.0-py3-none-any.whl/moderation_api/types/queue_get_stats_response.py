# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = [
    "QueueGetStatsResponse",
    "ActionStat",
    "ReviewStats",
    "TopReviewer",
    "TopReviewerTopAction",
    "Trends",
    "TrendsDailyReviewCount",
    "TrendsFlaggedContentTrend",
]


class ActionStat(BaseModel):
    action_id: str = FieldInfo(alias="actionId")
    """ID of the moderation action"""

    action_name: str = FieldInfo(alias="actionName")
    """Name of the moderation action"""

    count: float
    """Number of times this action was taken"""

    percentage_of_total: float = FieldInfo(alias="percentageOfTotal")
    """Percentage this action represents of all actions"""


class ReviewStats(BaseModel):
    average_time_to_review: float = FieldInfo(alias="averageTimeToReview")
    """Average time in milliseconds to review an item"""

    total_pending: float = FieldInfo(alias="totalPending")
    """Total number of items pending review"""

    total_reviewed: float = FieldInfo(alias="totalReviewed")
    """Total number of items reviewed"""


class TopReviewerTopAction(BaseModel):
    action_id: str = FieldInfo(alias="actionId")
    """Most used action by this reviewer"""

    action_name: str = FieldInfo(alias="actionName")
    """Name of the most used action"""

    count: float
    """Number of times this action was used"""


class TopReviewer(BaseModel):
    average_time_per_review: float = FieldInfo(alias="averageTimePerReview")
    """Average review time in milliseconds"""

    name: str
    """Name of the reviewer"""

    review_count: float = FieldInfo(alias="reviewCount")
    """Number of items reviewed"""

    top_actions: List[TopReviewerTopAction] = FieldInfo(alias="topActions")
    """Most common actions taken by this reviewer"""

    user_id: str = FieldInfo(alias="userId")
    """ID of the reviewer"""

    accuracy_score: Optional[float] = FieldInfo(alias="accuracyScore", default=None)
    """Optional accuracy score based on review quality metrics"""


class TrendsDailyReviewCount(BaseModel):
    count: float
    """Number of reviews on this date"""

    date: str
    """Date in YYYY-MM-DD format"""


class TrendsFlaggedContentTrend(BaseModel):
    label: str
    """Content flag/label"""

    trend: float
    """
    Trend indicator (-1 to 1) showing if this type of flagged content is increasing
    or decreasing
    """


class Trends(BaseModel):
    daily_review_counts: List[TrendsDailyReviewCount] = FieldInfo(alias="dailyReviewCounts")

    flagged_content_trends: List[TrendsFlaggedContentTrend] = FieldInfo(alias="flaggedContentTrends")


class QueueGetStatsResponse(BaseModel):
    action_stats: List[ActionStat] = FieldInfo(alias="actionStats")

    review_stats: ReviewStats = FieldInfo(alias="reviewStats")

    top_reviewers: List[TopReviewer] = FieldInfo(alias="topReviewers")
    """List of top reviewers and their statistics"""

    trends: Trends
