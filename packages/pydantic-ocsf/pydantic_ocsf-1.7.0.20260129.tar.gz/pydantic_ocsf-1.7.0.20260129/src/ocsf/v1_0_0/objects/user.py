"""User object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_0_0.enums.type_id import TypeId
    from ocsf.v1_0_0.objects.account import Account
    from ocsf.v1_0_0.objects.group import Group
    from ocsf.v1_0_0.objects.organization import Organization


class User(OCSFBaseModel):
    """The User object describes the characteristics of a user/person or a security principal. Defined by D3FEND <a target='_blank' href='https://d3fend.mitre.org/dao/artifact/d3f:UserAccount/'>d3f:UserAccount</a>.

    See: https://schema.ocsf.io/1.0.0/objects/user
    """

    type_id: TypeId = Field(..., description="The account type identifier.")
    account: Account | None = Field(
        default=None, description="The user's account or the account associated with the user."
    )
    credential_uid: str | None = Field(
        default=None,
        description="The unique identifier of the user's credential. For example, AWS Access Key ID.",
    )
    domain: str | None = Field(
        default=None,
        description="The domain where the user is defined. For example: the LDAP or Active Directory domain.",
    )
    email_addr: Any | None = Field(default=None, description="The user's email address.")
    full_name: str | None = Field(
        default=None,
        description="The full name of the person, as per the LDAP Common Name attribute (cn).",
    )
    groups: list[Group] | None = Field(
        default=None, description="The administrative groups to which the user belongs."
    )
    name: Any | None = Field(
        default=None, description="The username. For example, <code>janedoe1</code>."
    )
    org: Organization | None = Field(
        default=None, description="Organization and org unit related to the user."
    )
    type_: str | None = Field(
        default=None, description="The type of the user. For example, System, AWS IAM User, etc."
    )
    uid: str | None = Field(
        default=None,
        description="The unique user identifier. For example, the Windows user SID, ActiveDirectory DN or AWS user ARN.",
    )
    uid_alt: str | None = Field(
        default=None,
        description="The alternate user identifier. For example, the Active Directory user GUID or AWS user Principal ID.",
    )
