"""Ticket object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.enums.status_id import StatusId
    from ocsf.v1_6_0.enums.type_id import TypeId


class Ticket(OCSFBaseModel):
    """The Ticket object represents ticket in the customer's IT Service Management (ITSM) systems like ServiceNow, Jira, etc.

    See: https://schema.ocsf.io/1.6.0/objects/ticket
    """

    src_url: Any | None = Field(
        default=None, description="The url of a ticket in the ticket system. [Recommended]"
    )
    status: str | None = Field(
        default=None,
        description="The status of the ticket normalized to the caption of the <code>status_id</code> value. In the case of <code>99</code>, this value should as defined by the source.",
    )
    status_details: list[str] | None = Field(
        default=None,
        description="A list of contextual descriptions of the <code>status, status_id</code> values.",
    )
    status_id: StatusId | None = Field(
        default=None, description="The normalized identifier for the ticket status."
    )
    title: str | None = Field(default=None, description="The title of the ticket.")
    type_: str | None = Field(
        default=None,
        description="The linked ticket type determines whether the ticket is internal or in an external ticketing system.",
    )
    type_id: TypeId | None = Field(
        default=None, description="The normalized identifier for the ticket type."
    )
    uid: str | None = Field(
        default=None, description="Unique identifier of the ticket. [Recommended]"
    )
