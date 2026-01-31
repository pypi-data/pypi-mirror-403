"""Observable object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.enums.type_id import TypeId
    from ocsf.v1_7_0.objects.reputation import Reputation


class Observable(OCSFBaseModel):
    """The observable object is a pivot element that contains related information found in many places in the event.

    See: https://schema.ocsf.io/1.7.0/objects/observable
    """

    type_id: TypeId = Field(..., description="The observable value type identifier.")
    event_uid: str | None = Field(
        default=None,
        description="The unique identifier (<code>metadata.uid</code>) of the source OCSF event from which this observable was extracted. This field enables linking observables back to their originating event data when observables are stored in a separate location or system.",
    )
    name: str | None = Field(
        default=None,
        description="The full name of the observable attribute. The <code>name</code> is a pointer/reference to an attribute within the OCSF event data. For example: <code>file.name</code>. Array attributes may be represented in one of three ways. For example: <code>resources.uid</code>, <code>resources[].uid</code>, <code>resources[0].uid</code>. [Recommended]",
    )
    reputation: Reputation | None = Field(
        default=None, description="Contains the original and normalized reputation scores."
    )
    type_: str | None = Field(default=None, description="The observable value type name.")
    type_uid: int | None = Field(
        default=None,
        description="The OCSF event type UID (<code>type_uid</code>) of the source event that this observable was extracted from. This field enables filtering and categorizing observables by their originating event type. For example: <code>300101</code> for Network Activity (class_uid 3001) with activity_id 1.",
    )
    value: str | None = Field(
        default=None,
        description="The value associated with the observable attribute. The meaning of the value depends on the observable type.<br/>If the <code>name</code> refers to a scalar attribute, then the <code>value</code> is the value of the attribute.<br/>If the <code>name</code> refers to an object attribute, then the <code>value</code> is not populated.",
    )
