"""SCIM object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.enums.auth_protocol_id import AuthProtocolId
    from ocsf.v1_7_0.enums.state_id import StateId


class Scim(OCSFBaseModel):
    """The System for Cross-domain Identity Management (SCIM) Configuration object provides a structured set of attributes related to SCIM protocols used for identity provisioning and management across cloud-based platforms. It standardizes user and group provisioning details, enabling identity synchronization and lifecycle management with compatible Identity Providers (IdPs) and applications. SCIM is defined in <a target='_blank' href='https://datatracker.ietf.org/doc/html/rfc7643'>RFC-7634</a>

    See: https://schema.ocsf.io/1.7.0/objects/scim
    """

    auth_protocol: str | None = Field(
        default=None,
        description="The authorization protocol as defined by the caption of <code>auth_protocol_id</code>. In the case of <code>Other</code>, it is defined by the event source.",
    )
    auth_protocol_id: AuthProtocolId | None = Field(
        default=None,
        description="The normalized identifier of the authorization protocol used by the SCIM resource.",
    )
    created_time: int | None = Field(
        default=None, description="When the SCIM resource was added to the service provider."
    )
    error_message: str | None = Field(
        default=None, description="Message or code associated with the last encountered error."
    )
    is_group_provisioning_enabled: bool | None = Field(
        default=None,
        description="Indicates whether the SCIM resource is configured to provision groups, automatically or otherwise.",
    )
    is_user_provisioning_enabled: bool | None = Field(
        default=None,
        description="Indicates whether the SCIM resource is configured to provision users, automatically or otherwise.",
    )
    last_run_time: int | None = Field(
        default=None, description="Timestamp of the most recent successful synchronization."
    )
    modified_time: int | None = Field(
        default=None,
        description="The most recent time when the SCIM resource was updated at the service provider.",
    )
    name: str | None = Field(
        default=None, description="The name of the SCIM resource. [Recommended]"
    )
    protocol_name: str | None = Field(
        default=None,
        description="The supported protocol for the SCIM resource. E.g., <code>SAML</code>, <code>OIDC</code>, or <code>OAuth2</code>.",
    )
    rate_limit: int | None = Field(
        default=None,
        description="Maximum number of requests allowed by the SCIM resource within a specified time frame to avoid throttling.",
    )
    scim_group_schema: dict[str, Any] | None = Field(
        default=None,
        description="SCIM provides a schema for representing groups, identified using the following schema URI: <code>urn:ietf:params:scim:schemas:core:2.0:Group</code> as defined in <a target='_blank' href='https://datatracker.ietf.org/doc/html/rfc7643'>RFC-7634</a>. This attribute will capture key-value pairs for the scheme implemented in a SCIM resource. [Recommended]",
    )
    scim_user_schema: dict[str, Any] | None = Field(
        default=None,
        description="SCIM provides a resource type for user resources. The core schema for user is identified using the following schema URI: <code>urn:ietf:params:scim:schemas:core:2.0:User</code> as defined in <a target='_blank' href='https://datatracker.ietf.org/doc/html/rfc7643'>RFC-7634</a>. his attribute will capture key-value pairs for the scheme implemented in a SCIM resource. This object is inclusive of both the basic and Enterprise User Schema Extension. [Recommended]",
    )
    state: str | None = Field(
        default=None,
        description="The provisioning state of the SCIM resource, normalized to the caption of the <code>state_id</code> value. In the case of <code>Other</code>, it is defined by the event source.",
    )
    state_id: StateId | None = Field(
        default=None,
        description="The normalized state ID of the SCIM resource to reflect its activation status.",
    )
    uid: str | None = Field(
        default=None,
        description="A unique identifier for a SCIM resource as defined by the service provider. [Recommended]",
    )
    uid_alt: str | None = Field(
        default=None,
        description="A String that is an identifier for the resource as defined by the provisioning client. The <code>externalId</code> may simplify identification of a resource between the provisioning client and the service provider by allowing the client to use a filter to locate the resource with an identifier from the provisioning domain, obviating the need to store a local mapping between the provisioning domain's identifier of the resource and the identifier used by the service provider.",
    )
    url_string: Any | None = Field(
        default=None, description="The primary URL for SCIM API requests."
    )
    vendor_name: str | None = Field(
        default=None,
        description="Name of the vendor or service provider implementing SCIM. E.g., <code>Okta</code>, <code>Auth0</code>, <code>Microsoft</code>.",
    )
    version: str | None = Field(
        default=None,
        description="SCIM protocol version supported e.g., <code>SCIM 2.0</code>. [Recommended]",
    )
