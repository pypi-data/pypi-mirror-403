"""WHOIS object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.dnssec_status_id import DnssecStatusId
    from ocsf.v1_5_0.objects.autonomous_system import AutonomousSystem
    from ocsf.v1_5_0.objects.domain_contact import DomainContact


class Whois(OCSFBaseModel):
    """The resources of a WHOIS record for a given domain. This can include domain names, IP address blocks, autonomous system information, and/or contact and registration information for a domain.

    See: https://schema.ocsf.io/1.5.0/objects/whois
    """

    autonomous_system: AutonomousSystem | None = Field(
        default=None, description="The autonomous system information associated with a domain."
    )
    created_time: int | None = Field(
        default=None,
        description="When the domain was registered or WHOIS entry was created. [Recommended]",
    )
    dnssec_status: str | None = Field(
        default=None, description="The normalized value of dnssec_status_id."
    )
    dnssec_status_id: DnssecStatusId | None = Field(
        default=None,
        description="Describes the normalized status of DNS Security Extensions (DNSSEC) for a domain. [Recommended]",
    )
    domain: str | None = Field(
        default=None, description="The domain name corresponding to the WHOIS record. [Recommended]"
    )
    domain_contacts: list[DomainContact] | None = Field(
        default=None, description="An array of <code>Domain Contact</code> objects. [Recommended]"
    )
    email_addr: Any | None = Field(
        default=None, description="The email address for the registrar's abuse contact"
    )
    isp: str | None = Field(
        default=None, description="The name of the Internet Service Provider (ISP)."
    )
    isp_org: str | None = Field(
        default=None,
        description="The organization name of the Internet Service Provider (ISP). This represents the parent organization or company that owns/operates the ISP. For example, Comcast Corporation would be the ISP org for Xfinity internet service. This attribute helps identify the ultimate provider when ISPs operate under different brand names.",
    )
    last_seen_time: int | None = Field(
        default=None, description="When the WHOIS record was last updated or seen at. [Recommended]"
    )
    name_servers: list[str] | None = Field(
        default=None,
        description="A collection of name servers related to a domain registration or other record. [Recommended]",
    )
    phone_number: str | None = Field(
        default=None, description="The phone number for the registrar's abuse contact"
    )
    registrar: str | None = Field(default=None, description="The domain registrar. [Recommended]")
    status: str | None = Field(
        default=None,
        description="The status of a domain and its ability to be transferred, e.g., <code>clientTransferProhibited</code>. [Recommended]",
    )
    subdomains: list[str] | None = Field(
        default=None,
        description="An array of subdomain strings. Can be used to collect several subdomains such as those from Domain Generation Algorithms (DGAs).",
    )
    subnet: Any | None = Field(
        default=None, description="The IP address block (CIDR) associated with a domain."
    )
