"""Identity Provider object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.state_id import StateId
    from ocsf.v1_5_0.objects.auth_factor import AuthFactor
    from ocsf.v1_5_0.objects.fingerprint import Fingerprint
    from ocsf.v1_5_0.objects.scim import Scim
    from ocsf.v1_5_0.objects.sso import Sso


class Idp(OCSFBaseModel):
    """The Identity Provider object contains detailed information about a provider responsible for creating, maintaining, and managing identity information while offering authentication services to applications. An Identity Provider (IdP) serves as a trusted authority that verifies the identity of users and issues authentication tokens or assertions to enable secure access to applications or services.

    See: https://schema.ocsf.io/1.5.0/objects/idp
    """

    auth_factors: list[AuthFactor] | None = Field(
        default=None,
        description="The Authentication Factors object describes the different types of Multi-Factor Authentication (MFA) methods and/or devices supported by the Identity Provider.",
    )
    domain: str | None = Field(
        default=None, description="The primary domain associated with the Identity Provider."
    )
    fingerprint: Fingerprint | None = Field(
        default=None,
        description="The fingerprint of the X.509 certificate used by the Identity Provider.",
    )
    has_mfa: bool | None = Field(
        default=None,
        description="The Identity Provider enforces Multi Factor Authentication (MFA).",
    )
    issuer: str | None = Field(
        default=None,
        description="The unique identifier (often a URL) used by the Identity Provider as its issuer.",
    )
    name: str | None = Field(
        default=None, description="The name of the Identity Provider. [Recommended]"
    )
    protocol_name: str | None = Field(
        default=None,
        description="The supported protocol of the Identity Provider. E.g., <code>SAML</code>, <code>OIDC</code>, or <code>OAuth2</code>.",
    )
    scim: Scim | None = Field(
        default=None,
        description="The System for Cross-domain Identity Management (SCIM) resource object provides a structured set of attributes related to SCIM protocols used for identity provisioning and management across cloud-based platforms. It standardizes user and group provisioning details, enabling identity synchronization and lifecycle management with compatible Identity Providers (IdPs) and applications. SCIM is defined in <a target='_blank' href='https://datatracker.ietf.org/doc/html/rfc7643'>RFC-7634</a>",
    )
    sso: Sso | None = Field(
        default=None,
        description="The Single Sign-On (SSO) object provides a structure for normalizing SSO attributes, configuration, and/or settings from Identity Providers.",
    )
    state: str | None = Field(
        default=None,
        description="The configuration state of the Identity Provider, normalized to the caption of the <code>state_id</code> value. In the case of <code>Other</code>, it is defined by the event source.",
    )
    state_id: StateId | None = Field(
        default=None,
        description="The normalized state ID of the Identity Provider to reflect its configuration or activation status.",
    )
    tenant_uid: str | None = Field(
        default=None, description="The tenant ID associated with the Identity Provider."
    )
    uid: str | None = Field(
        default=None, description="The unique identifier of the Identity Provider. [Recommended]"
    )
    url_string: Any | None = Field(
        default=None,
        description="The URL for accessing the configuration or metadata of the Identity Provider.",
    )
