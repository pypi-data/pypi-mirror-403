# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["ItemUnresolveParams"]


class ItemUnresolveParams(TypedDict, total=False):
    id: Required[str]
    """The queue ID"""

    comment: str
    """Optional reason for unresolving the item"""
