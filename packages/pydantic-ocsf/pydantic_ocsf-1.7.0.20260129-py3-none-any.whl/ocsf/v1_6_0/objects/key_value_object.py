"""Key:Value object object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class KeyValueObject(OCSFBaseModel):
    """A generic object allowing to define a <code>{key:value}</code> pair.

    See: https://schema.ocsf.io/1.6.0/objects/key_value_object
    """

    name: str = Field(..., description="The name of the key.")
    value: str | None = Field(
        default=None, description="The value associated to the key. [Recommended]"
    )
    values: list[str] | None = Field(
        default=None,
        description="Optional, the values associated to the key. You can populate this attribute, when you have multiple values for the same key. [Recommended]",
    )
