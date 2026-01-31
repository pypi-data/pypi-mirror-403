# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .._models import BaseModel

__all__ = ["ActionDeleteResponse"]


class ActionDeleteResponse(BaseModel):
    id: str
    """The ID of the action."""

    deleted: bool
    """Whether the action was deleted."""
