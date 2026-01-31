"""Observable object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_0_0.enums.type_id import TypeId
    from ocsf.v1_0_0.objects.reputation import Reputation


class Observable(OCSFBaseModel):
    """The observable object is a pivot element that contains related information found in many places in the event.

    See: https://schema.ocsf.io/1.0.0/objects/observable
    """

    name: str = Field(
        ...,
        description="The full name of the observable attribute. The <code>name</code> is a pointer/reference to an attribute within the event data. For example: <code>file.name</code>.",
    )
    type_id: TypeId = Field(..., description="The observable value type identifier.")
    reputation: Reputation | None = Field(
        default=None, description="Contains the original and normalized reputation scores."
    )
    type_: str | None = Field(default=None, description="The observable value type name.")
    value: str | None = Field(
        default=None,
        description="The value associated with the observable attribute. The meaning of the value depends on the observable type.<br/>If the <code>name</code> refers to a scalar attribute, then the <code>value</code> is the value of the attribute.<br/>If the <code>name</code> refers to an object attribute, then the <code>value</code> is not populated.",
    )
