"""Analytic object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.type_id import TypeId


class Analytic(OCSFBaseModel):
    """The Analytic object contains details about the analytic technique used to analyze and derive insights from the data or information that led to the creation of a finding or conclusion.

    See: https://schema.ocsf.io/1.5.0/objects/analytic
    """

    type_id: TypeId = Field(..., description="The analytic type ID.")
    algorithm: str | None = Field(
        default=None,
        description="The algorithm used by the underlying analytic to generate the finding.",
    )
    category: str | None = Field(default=None, description="The analytic category.")
    desc: str | None = Field(
        default=None, description="The description of the analytic that generated the finding."
    )
    name: str | None = Field(
        default=None, description="The name of the analytic that generated the finding."
    )
    related_analytics: list[Analytic] | None = Field(
        default=None, description="Other analytics related to this analytic."
    )
    type_: str | None = Field(default=None, description="The analytic type.")
    uid: str | None = Field(
        default=None,
        description="The unique identifier of the analytic that generated the finding.",
    )
    version: str | None = Field(
        default=None, description="The analytic version. For example: <code>1.1</code>."
    )
