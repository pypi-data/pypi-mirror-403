# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable, Optional
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["ActionCreateParams", "PossibleValue", "Webhook"]


class ActionCreateParams(TypedDict, total=False):
    name: Required[str]
    """The name of the action."""

    built_in: Annotated[Optional[bool], PropertyInfo(alias="builtIn")]
    """Whether the action is a built-in action or a custom one."""

    description: Optional[str]
    """The description of the action."""

    filter_in_queue_ids: Annotated[SequenceNotStr[str], PropertyInfo(alias="filterInQueueIds")]
    """The IDs of the queues the action is available in."""

    free_text: Annotated[bool, PropertyInfo(alias="freeText")]
    """
    Whether the action allows any text to be entered as a value or if it must be one
    of the possible values.
    """

    key: Optional[str]
    """User defined key of the action."""

    position: Literal["ALL_QUEUES", "SOME_QUEUES", "HIDDEN"]
    """
    Show the action in all queues, selected queues or no queues (to use via API
    only).
    """

    possible_values: Annotated[Iterable[PossibleValue], PropertyInfo(alias="possibleValues")]
    """The possible values of the action.

    The user will be prompted to select one of these values when executing the
    action.
    """

    queue_behaviour: Annotated[Literal["REMOVE", "ADD", "NO_CHANGE"], PropertyInfo(alias="queueBehaviour")]
    """
    Whether the action resolves and removes the item, unresolves and re-add it to
    the queue, or does not change the resolve status.
    """

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
    ]
    """The type of the action."""

    value_required: Annotated[bool, PropertyInfo(alias="valueRequired")]
    """Whether the action requires a value to be executed."""

    webhooks: Iterable[Webhook]
    """The action's webhooks."""


class PossibleValue(TypedDict, total=False):
    value: Required[str]
    """The value of the action."""


class Webhook(TypedDict, total=False):
    name: Required[str]
    """The webhook's name, used to identify it in the dashboard"""

    url: Required[str]
    """The webhook's URL. We'll call this URL when the event occurs."""

    id: str
    """ID of an existing webhook or undefined if this is a new webhook."""

    description: Optional[str]
    """The webhook's description"""
