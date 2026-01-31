"""Entity object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Entity(OCSFBaseModel):
    """The Entity object is an unordered collection of attributes, with a name and unique identifier. It serves as a base object that defines a set of attributes and default constraints available in all objects that extend it.

    See: https://schema.ocsf.io/1.0.0/objects/_entity
    """

    name: str | None = Field(default=None, description="The name of the entity. [Recommended]")
    uid: str | None = Field(
        default=None, description="The unique identifier of the entity. [Recommended]"
    )
