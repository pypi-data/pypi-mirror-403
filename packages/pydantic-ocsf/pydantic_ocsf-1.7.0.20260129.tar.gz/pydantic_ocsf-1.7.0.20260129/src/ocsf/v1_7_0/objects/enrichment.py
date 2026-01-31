"""Enrichment object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.objects.reputation import Reputation


class Enrichment(OCSFBaseModel):
    """The Enrichment object provides inline enrichment data for specific attributes of interest within an event. It serves as a mechanism to enhance or supplement the information associated with the event by adding additional relevant details or context.

    See: https://schema.ocsf.io/1.7.0/objects/enrichment
    """

    data: dict[str, Any] = Field(
        ...,
        description="The enrichment data associated with the attribute and value. The meaning of this data depends on the type the enrichment record.",
    )
    name: str = Field(
        ..., description="The name of the attribute to which the enriched data pertains."
    )
    value: str = Field(
        ..., description="The value of the attribute to which the enriched data pertains."
    )
    created_time: int | None = Field(
        default=None, description="The time when the enrichment data was generated. [Recommended]"
    )
    desc: str | None = Field(default=None, description="A long description of the enrichment data.")
    provider: str | None = Field(
        default=None, description="The enrichment data provider name. [Recommended]"
    )
    reputation: Reputation | None = Field(
        default=None, description="The reputation of the enrichment data."
    )
    short_desc: str | None = Field(
        default=None, description="A short description of the enrichment data. [Recommended]"
    )
    src_url: Any | None = Field(
        default=None, description="The URL of the source of the enrichment data. [Recommended]"
    )
    type_: str | None = Field(
        default=None,
        description="The enrichment type. For example: <code>location</code>. [Recommended]",
    )
