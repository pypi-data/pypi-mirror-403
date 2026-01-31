# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["AccountListResponse", "CurrentProject"]


class CurrentProject(BaseModel):
    id: str
    """ID of the current project"""

    name: str
    """Name of the current project"""


class AccountListResponse(BaseModel):
    id: str
    """ID of the account"""

    paid_plan_name: str
    """Name of the paid plan"""

    remaining_quota: float
    """Remaining quota"""

    text_api_quota: float
    """Text API quota"""

    current_project: Optional[CurrentProject] = None
