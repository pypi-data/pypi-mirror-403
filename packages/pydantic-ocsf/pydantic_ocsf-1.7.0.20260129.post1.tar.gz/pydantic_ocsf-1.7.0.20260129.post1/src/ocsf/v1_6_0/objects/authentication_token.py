"""Authentication Token object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.enums.type_id import TypeId
    from ocsf.v1_6_0.objects.encryption_details import EncryptionDetails


class AuthenticationToken(OCSFBaseModel):
    """The Authentication Token object represents standardized authentication tokens, tickets, or assertions that conform to established authentication protocols such as Kerberos, OIDC, and SAML. These tokens are issued by authentication servers and identity providers and carry protocol-specific metadata, lifecycle information, and security attributes defined by their respective specifications.

    See: https://schema.ocsf.io/1.6.0/objects/authentication_token
    """

    created_time: int | None = Field(
        default=None,
        description="The time that the authentication token was created. [Recommended]",
    )
    encryption_details: EncryptionDetails | None = Field(
        default=None,
        description="The encryption details of the authentication token. [Recommended]",
    )
    expiration_time: int | None = Field(
        default=None, description="The expiration time of the authentication token."
    )
    is_renewable: bool | None = Field(
        default=None, description="Indicates whether the authentication token is renewable."
    )
    kerberos_flags: str | None = Field(
        default=None,
        description="A bitmask, either in hexadecimal or decimal form, which encodes various attributes or permissions associated with a Kerberos ticket. These flags delineate specific characteristics of the ticket, such as its renewability or forwardability. [Recommended]",
    )
    type_: str | None = Field(
        default=None, description="The type of the authentication token. [Recommended]"
    )
    type_id: TypeId | None = Field(
        default=None,
        description="The normalized authentication token type identifier. [Recommended]",
    )
