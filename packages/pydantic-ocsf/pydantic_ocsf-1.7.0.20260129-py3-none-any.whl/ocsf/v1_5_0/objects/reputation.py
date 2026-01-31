"""Reputation object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.score_id import ScoreId


class Reputation(OCSFBaseModel):
    """The Reputation object describes the reputation/risk score of an entity (e.g. device, user, domain).

    See: https://schema.ocsf.io/1.5.0/objects/reputation
    """

    base_score: float = Field(
        ..., description="The reputation score as reported by the event source."
    )
    score_id: ScoreId = Field(..., description="The normalized reputation score identifier.")
    provider: str | None = Field(
        default=None, description="The provider of the reputation information. [Recommended]"
    )
    score: str | None = Field(
        default=None,
        description="The reputation score, normalized to the caption of the score_id value. In the case of 'Other', it is defined by the event source.",
    )
