"""Organization object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Organization(OCSFBaseModel):
    """The Organization object describes characteristics of an organization or company and its division if any.

    See: https://schema.ocsf.io/1.2.0/objects/organization
    """

    name: str | None = Field(
        default=None, description="The name of the organization. For example, Widget, Inc."
    )
    ou_name: str | None = Field(
        default=None,
        description="The name of the organizational unit, within an organization.  For example, Finance, IT, R&D [Recommended]",
    )
    ou_uid: str | None = Field(
        default=None,
        description="The alternate identifier for an entity's unique identifier. For example, its Active Directory OU DN or AWS OU ID.",
    )
    uid: str | None = Field(
        default=None,
        description="The unique identifier of the organization. For example, its Active Directory or AWS Org ID.",
    )
