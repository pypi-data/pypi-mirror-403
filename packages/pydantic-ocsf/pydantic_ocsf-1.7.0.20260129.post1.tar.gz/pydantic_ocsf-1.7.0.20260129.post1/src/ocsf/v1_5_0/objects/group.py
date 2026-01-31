"""Group object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Group(OCSFBaseModel):
    """The Group object represents a collection or association of entities, such as users, policies, or devices. It serves as a logical grouping mechanism to organize and manage entities with similar characteristics or permissions within a system or organization, including but not limited to purposes of access control.

    See: https://schema.ocsf.io/1.5.0/objects/group
    """

    desc: str | None = Field(default=None, description="The group description.")
    domain: str | None = Field(
        default=None,
        description="The domain where the group is defined. For example: the LDAP or Active Directory domain.",
    )
    name: str | None = Field(default=None, description="The group name.")
    privileges: list[str] | None = Field(default=None, description="The group privileges.")
    type_: str | None = Field(default=None, description="The type of the group or account.")
    uid: str | None = Field(
        default=None,
        description="The unique identifier of the group. For example, for Windows events this is the security identifier (SID) of the group.",
    )
