"""SSO object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.enums.auth_protocol_id import AuthProtocolId
    from ocsf.v1_6_0.objects.certificate import Certificate


class Sso(OCSFBaseModel):
    """The Single Sign-On (SSO) object provides a structure for normalizing SSO attributes, configuration, and/or settings from Identity Providers.

    See: https://schema.ocsf.io/1.6.0/objects/sso
    """

    auth_protocol: str | None = Field(
        default=None,
        description="The authorization protocol as defined by the caption of <code>auth_protocol_id</code>. In the case of <code>Other</code>, it is defined by the event source.",
    )
    auth_protocol_id: AuthProtocolId | None = Field(
        default=None,
        description="The normalized identifier of the authentication protocol used by the SSO resource.",
    )
    certificate: Certificate | None = Field(
        default=None,
        description="Digital Signature associated with the SSO resource, e.g., SAML X.509 certificate details. [Recommended]",
    )
    created_time: int | None = Field(default=None, description="When the SSO resource was created.")
    duration_mins: int | None = Field(
        default=None,
        description="The duration (in minutes) for an SSO session, after which re-authentication is required.",
    )
    idle_timeout: int | None = Field(
        default=None,
        description="Duration (in minutes) of allowed inactivity before Single Sign-On (SSO) session expiration.",
    )
    login_endpoint: Any | None = Field(
        default=None, description="URL for initiating an SSO login request."
    )
    logout_endpoint: Any | None = Field(
        default=None,
        description="URL for initiating an SSO logout request, allowing sessions to be terminated across applications.",
    )
    metadata_endpoint: Any | None = Field(
        default=None,
        description="URL where metadata about the SSO configuration is available (e.g., for SAML configurations).",
    )
    modified_time: int | None = Field(
        default=None, description="The most recent time when the SSO resource was updated."
    )
    name: str | None = Field(
        default=None, description="The name of the SSO resource. [Recommended]"
    )
    protocol_name: str | None = Field(
        default=None,
        description="The supported protocol for the SSO resource. E.g., <code>SAML</code> or <code>OIDC</code>.",
    )
    scopes: list[str] | None = Field(
        default=None,
        description="Scopes define the specific permissions or actions that the client is allowed to perform on behalf of the user. Each scope represents a different set of permissions, and the user can selectively grant or deny access to specific scopes during the authorization process.",
    )
    uid: str | None = Field(
        default=None, description="A unique identifier for a SSO resource. [Recommended]"
    )
    vendor_name: str | None = Field(
        default=None,
        description="Name of the vendor or service provider implementing SSO. E.g., <code>Okta</code>, <code>Auth0</code>, <code>Microsoft</code>.",
    )
