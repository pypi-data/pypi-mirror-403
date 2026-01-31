"""User object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.enums.risk_level_id import RiskLevelId
    from ocsf.v1_7_0.enums.type_id import TypeId
    from ocsf.v1_7_0.objects.account import Account
    from ocsf.v1_7_0.objects.group import Group
    from ocsf.v1_7_0.objects.ldap_person import LdapPerson
    from ocsf.v1_7_0.objects.organization import Organization
    from ocsf.v1_7_0.objects.programmatic_credential import ProgrammaticCredential


class User(OCSFBaseModel):
    """The User object describes the characteristics of a user/person or a security principal.

    See: https://schema.ocsf.io/1.7.0/objects/user
    """

    account: Account | None = Field(
        default=None, description="The user's account or the account associated with the user."
    )
    credential_uid: str | None = Field(
        default=None,
        description="The unique identifier of the user's credential. For example, AWS Access Key ID.",
    )
    display_name: str | None = Field(
        default=None, description="The display name of the user, as reported by the product."
    )
    domain: str | None = Field(
        default=None,
        description="The domain where the user is defined. For example: the LDAP or Active Directory domain.",
    )
    email_addr: Any | None = Field(default=None, description="The user's primary email address.")
    forward_addr: Any | None = Field(
        default=None, description="The user's forwarding email address."
    )
    full_name: str | None = Field(
        default=None, description="The full name of the user, as reported by the product."
    )
    groups: list[Group] | None = Field(
        default=None, description="The administrative groups to which the user belongs."
    )
    has_mfa: bool | None = Field(
        default=None,
        description="The user has a multi-factor or secondary-factor device assigned. [Recommended]",
    )
    ldap_person: LdapPerson | None = Field(
        default=None, description="The additional LDAP attributes that describe a person."
    )
    name: Any | None = Field(
        default=None, description="The username. For example, <code>janedoe1</code>. [Recommended]"
    )
    org: Organization | None = Field(
        default=None, description="Organization and org unit related to the user."
    )
    phone_number: str | None = Field(default=None, description="The telephone number of the user.")
    programmatic_credentials: list[ProgrammaticCredential] | None = Field(
        default=None,
        description="Details about the programmatic credential (API keys, access tokens, certificates, etc) associated to the user.",
    )
    risk_level: str | None = Field(
        default=None,
        description="The risk level, normalized to the caption of the risk_level_id value.",
    )
    risk_level_id: RiskLevelId | None = Field(
        default=None, description="The normalized risk level id."
    )
    risk_score: int | None = Field(
        default=None, description="The risk score as reported by the event source."
    )
    type_: str | None = Field(
        default=None, description="The type of the user. For example, System, AWS IAM User, etc."
    )
    type_id: TypeId | None = Field(
        default=None, description="The account type identifier. [Recommended]"
    )
    uid: str | None = Field(
        default=None,
        description="The unique user identifier. For example, the Windows user SID, ActiveDirectory DN or AWS user ARN. [Recommended]",
    )
    uid_alt: str | None = Field(
        default=None,
        description="The alternate user identifier. For example, the Active Directory user GUID or AWS user Principal ID.",
    )
