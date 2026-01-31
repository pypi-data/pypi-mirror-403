# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import TYPE_CHECKING, Dict, List, Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = [
    "AuthorListResponse",
    "Author",
    "AuthorBlock",
    "AuthorMetadata",
    "AuthorMetrics",
    "AuthorRiskEvaluation",
    "AuthorTrustLevel",
    "Pagination",
]


class AuthorBlock(BaseModel):
    """Block or suspension details, if applicable. Null if the author is enabled."""

    reason: Optional[str] = None
    """The moderators reason why the author was blocked or suspended."""

    until: Optional[float] = None
    """The timestamp until which they are blocked if the author is suspended."""


class AuthorMetadata(BaseModel):
    """Additional metadata provided by your system.

    We recommend including any relevant information that may assist in the moderation process.
    """

    email_verified: Optional[bool] = None
    """Whether the author's email is verified"""

    identity_verified: Optional[bool] = None
    """Whether the author's identity is verified"""

    is_paying_customer: Optional[bool] = None
    """Whether the author is a paying customer"""

    phone_verified: Optional[bool] = None
    """Whether the author's phone number is verified"""

    if TYPE_CHECKING:
        # Some versions of Pydantic <2.8.0 have a bug and don’t allow assigning a
        # value to this field, so for compatibility we avoid doing it at runtime.
        __pydantic_extra__: Dict[str, object] = FieldInfo(init=False)  # pyright: ignore[reportIncompatibleVariableOverride]

        # Stub to indicate that arbitrary properties are accepted.
        # To access properties that are not valid identifiers you can use `getattr`, e.g.
        # `getattr(obj, '$type')`
        def __getattr__(self, attr: str) -> object: ...
    else:
        __pydantic_extra__: Dict[str, object]


class AuthorMetrics(BaseModel):
    flagged_content: float
    """Number of flagged content pieces"""

    total_content: float
    """Total pieces of content"""

    average_sentiment: Optional[float] = None
    """Average sentiment score of content (-1 to 1).

    Requires a sentiment model in your project.
    """


class AuthorRiskEvaluation(BaseModel):
    """Risk assessment details, if available."""

    risk_level: Optional[float] = None
    """Calculated risk level based on more than 10 behavioral signals."""


class AuthorTrustLevel(BaseModel):
    level: float
    """Author trust level (-1, 0, 1, 2, 3, or 4)"""

    manual: bool
    """True if the trust level was set manually by a moderator"""


class Author(BaseModel):
    id: str
    """Author ID in Moderation API"""

    block: Optional[AuthorBlock] = None
    """Block or suspension details, if applicable. Null if the author is enabled."""

    first_seen: float
    """Timestamp when author first appeared"""

    last_seen: float
    """Timestamp of last activity"""

    metadata: AuthorMetadata
    """Additional metadata provided by your system.

    We recommend including any relevant information that may assist in the
    moderation process.
    """

    metrics: AuthorMetrics

    risk_evaluation: Optional[AuthorRiskEvaluation] = None
    """Risk assessment details, if available."""

    status: Literal["enabled", "suspended", "blocked"]
    """Current author status"""

    trust_level: AuthorTrustLevel

    email: Optional[str] = None
    """Author email address"""

    external_id: Optional[str] = None
    """The author's ID from your system"""

    external_link: Optional[str] = None
    """URL of the author's external profile"""

    last_incident: Optional[float] = None
    """Timestamp of last incident"""

    name: Optional[str] = None
    """Author name or identifier"""

    profile_picture: Optional[str] = None
    """URL of the author's profile picture"""


class Pagination(BaseModel):
    has_next_page: bool = FieldInfo(alias="hasNextPage")

    has_previous_page: bool = FieldInfo(alias="hasPreviousPage")

    page_number: float = FieldInfo(alias="pageNumber")

    page_size: float = FieldInfo(alias="pageSize")

    total: float


class AuthorListResponse(BaseModel):
    authors: List[Author]

    pagination: Pagination
