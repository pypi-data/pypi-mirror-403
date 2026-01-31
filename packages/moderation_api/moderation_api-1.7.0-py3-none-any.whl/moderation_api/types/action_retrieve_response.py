# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["ActionRetrieveResponse", "PossibleValue", "Webhook"]


class PossibleValue(BaseModel):
    value: str
    """The value of the action."""


class Webhook(BaseModel):
    id: str
    """The ID of the webhook."""

    name: str
    """The webhook's name, used to identify it in the dashboard"""

    url: str
    """The webhook's URL. We'll call this URL when the event occurs."""

    description: Optional[str] = None
    """The webhook's description"""

    moderation_action_id: Optional[str] = FieldInfo(alias="moderationActionId", default=None)
    """The ID of the moderation action to trigger the webhook on.

    Only used for moderation action webhooks.
    """


class ActionRetrieveResponse(BaseModel):
    id: str
    """The ID of the action."""

    built_in: Optional[bool] = FieldInfo(alias="builtIn", default=None)
    """Whether the action is a built-in action or a custom one."""

    created_at: str = FieldInfo(alias="createdAt")
    """The date the action was created."""

    filter_in_queue_ids: List[str] = FieldInfo(alias="filterInQueueIds")
    """The IDs of the queues the action is available in."""

    free_text: bool = FieldInfo(alias="freeText")
    """
    Whether the action allows any text to be entered as a value or if it must be one
    of the possible values.
    """

    name: str
    """The name of the action."""

    position: Literal["ALL_QUEUES", "SOME_QUEUES", "HIDDEN"]
    """
    Show the action in all queues, selected queues or no queues (to use via API
    only).
    """

    possible_values: List[PossibleValue] = FieldInfo(alias="possibleValues")
    """The possible values of the action.

    The user will be prompted to select one of these values when executing the
    action.
    """

    queue_behaviour: Literal["REMOVE", "ADD", "NO_CHANGE"] = FieldInfo(alias="queueBehaviour")
    """
    Whether the action resolves and removes the item, unresolves and re-add it to
    the queue, or does not change the resolve status.
    """

    value_required: bool = FieldInfo(alias="valueRequired")
    """Whether the action requires a value to be executed."""

    webhooks: List[Webhook]
    """The action's webhooks."""

    description: Optional[str] = None
    """The description of the action."""

    key: Optional[str] = None
    """User defined key of the action."""

    type: Optional[
        Literal[
            "AUTHOR_BLOCK",
            "AUTHOR_BLOCK_TEMP",
            "AUTHOR_UNBLOCK",
            "AUTHOR_DELETE",
            "AUTHOR_REPORT",
            "AUTHOR_WARN",
            "AUTHOR_CUSTOM",
            "ITEM_REJECT",
            "ITEM_ALLOW",
            "ITEM_CUSTOM",
        ]
    ] = None
    """The type of the action."""
