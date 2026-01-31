# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from ..._models import BaseModel

__all__ = ["ExecuteExecuteResponse"]


class ExecuteExecuteResponse(BaseModel):
    """Execution result"""

    success: bool
    """Whether the action was executed successfully"""
