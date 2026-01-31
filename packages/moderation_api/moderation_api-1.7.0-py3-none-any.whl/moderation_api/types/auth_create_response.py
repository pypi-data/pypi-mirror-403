# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .._models import BaseModel

__all__ = ["AuthCreateResponse"]


class AuthCreateResponse(BaseModel):
    message: str
    """Message of the authentication"""

    project: str
    """Name of the authenticated project"""

    status: str
    """Status of the authentication"""
