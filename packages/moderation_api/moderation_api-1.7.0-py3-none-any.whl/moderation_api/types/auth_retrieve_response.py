# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .._models import BaseModel

__all__ = ["AuthRetrieveResponse"]


class AuthRetrieveResponse(BaseModel):
    message: str
    """Message of the authentication"""

    status: str
    """Status of the authentication"""
