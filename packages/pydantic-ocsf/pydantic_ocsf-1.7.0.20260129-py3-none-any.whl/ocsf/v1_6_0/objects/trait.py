"""Trait object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Trait(OCSFBaseModel):
    """Describes a characteristic or feature of an entity that was observed. For example, this object can be used to represent specific characteristics derived from events or findings that can be surfaced as distinguishing traits of the entity in question.

    See: https://schema.ocsf.io/1.6.0/objects/trait
    """

    category: str | None = Field(
        default=None, description="The high-level grouping or classification this trait belongs to."
    )
    name: str | None = Field(default=None, description="The name of the trait.")
    type_: str | None = Field(
        default=None,
        description="The type of the trait. For example, this can be used to indicate if the trait acts as a contributing factor (increases risk/severity) or a mitigating factor (decreases risk/severity), in the context of the related finding.",
    )
    uid: str | None = Field(default=None, description="The unique identifier of the trait.")
    values: list[str] | None = Field(default=None, description="The values of the trait.")
