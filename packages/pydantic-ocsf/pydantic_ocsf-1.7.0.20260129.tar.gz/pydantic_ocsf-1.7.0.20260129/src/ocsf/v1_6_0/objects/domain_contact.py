"""Domain Contact object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.enums.type_id import TypeId
    from ocsf.v1_6_0.objects.location import Location


class DomainContact(OCSFBaseModel):
    """The contact information related to a domain registration, e.g., registrant, administrator, abuse, billing, or technical contact.

    See: https://schema.ocsf.io/1.6.0/objects/domain_contact
    """

    type_id: TypeId = Field(..., description="The normalized domain contact type ID.")
    email_addr: Any | None = Field(
        default=None, description="The user's primary email address. [Recommended]"
    )
    location: Location | None = Field(
        default=None,
        description="Location details for the contract such as the city, state/province, country, etc. [Recommended]",
    )
    name: str | None = Field(
        default=None, description="The individual or organization name for the contact."
    )
    phone_number: str | None = Field(
        default=None, description="The number associated with the phone."
    )
    type_: str | None = Field(
        default=None,
        description="The Domain Contact type, normalized to the caption of the <code>type_id</code> value. In the case of 'Other', it is defined by the source",
    )
    uid: str | None = Field(
        default=None,
        description="The unique identifier of the contact information, typically provided in WHOIS information.",
    )
