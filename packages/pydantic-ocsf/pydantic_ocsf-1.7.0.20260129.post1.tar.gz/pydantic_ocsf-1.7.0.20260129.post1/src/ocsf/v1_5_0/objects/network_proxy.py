"""Network Proxy Endpoint object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.type_id import TypeId
    from ocsf.v1_5_0.objects.agent import Agent
    from ocsf.v1_5_0.objects.autonomous_system import AutonomousSystem
    from ocsf.v1_5_0.objects.device_hw_info import DeviceHwInfo
    from ocsf.v1_5_0.objects.location import Location
    from ocsf.v1_5_0.objects.os import Os
    from ocsf.v1_5_0.objects.user import User


class NetworkProxy(OCSFBaseModel):
    """The network proxy endpoint object describes a proxy server, which acts as an intermediary between a client requesting a resource and the server providing that resource.

    See: https://schema.ocsf.io/1.5.0/objects/network_proxy
    """

    agent_list: list[Agent] | None = Field(
        default=None,
        description="A list of <code>agent</code> objects associated with a device, endpoint, or resource.",
    )
    autonomous_system: AutonomousSystem | None = Field(
        default=None, description="The Autonomous System details associated with an IP address."
    )
    domain: str | None = Field(
        default=None,
        description="The name of the domain that the endpoint belongs to or that corresponds to the endpoint.",
    )
    hostname: Any | None = Field(
        default=None, description="The fully qualified name of the endpoint. [Recommended]"
    )
    hw_info: DeviceHwInfo | None = Field(
        default=None, description="The endpoint hardware information."
    )
    include: str | None = Field(default=None, description="")
    instance_uid: str | None = Field(
        default=None, description="The unique identifier of a VM instance. [Recommended]"
    )
    interface_name: str | None = Field(
        default=None, description="The name of the network interface (e.g. eth2). [Recommended]"
    )
    interface_uid: str | None = Field(
        default=None, description="The unique identifier of the network interface. [Recommended]"
    )
    intermediate_ips: list[Any] | None = Field(
        default=None,
        description="The intermediate IP Addresses. For example, the IP addresses in the HTTP X-Forwarded-For header.",
    )
    ip: Any | None = Field(
        default=None,
        description="The IP address of the endpoint, in either IPv4 or IPv6 format. [Recommended]",
    )
    isp: str | None = Field(
        default=None, description="The name of the Internet Service Provider (ISP)."
    )
    isp_org: str | None = Field(
        default=None,
        description="The organization name of the Internet Service Provider (ISP). This represents the parent organization or company that owns/operates the ISP. For example, Comcast Corporation would be the ISP org for Xfinity internet service. This attribute helps identify the ultimate provider when ISPs operate under different brand names.",
    )
    location: Location | None = Field(
        default=None, description="The geographical location of the endpoint."
    )
    mac: Any | None = Field(
        default=None, description="The Media Access Control (MAC) address of the endpoint."
    )
    name: str | None = Field(default=None, description="The short name of the endpoint.")
    os: Os | None = Field(default=None, description="The endpoint operating system.")
    owner: User | None = Field(
        default=None,
        description="The identity of the service or user account that owns the endpoint or was last logged into it. [Recommended]",
    )
    port: Any | None = Field(
        default=None,
        description="The port used for communication within the network connection. [Recommended]",
    )
    proxy_endpoint: NetworkProxy | None = Field(
        default=None,
        description="The network proxy information pertaining to a specific endpoint. This can be used to describe information pertaining to network address translation (NAT).",
    )
    subnet_uid: str | None = Field(
        default=None, description="The unique identifier of a virtual subnet."
    )
    svc_name: str | None = Field(
        default=None,
        description="The service name in service-to-service connections. For example, AWS VPC logs the pkt-src-aws-service and pkt-dst-aws-service fields identify the connection is coming from or going to an AWS service. [Recommended]",
    )
    type_: str | None = Field(
        default=None,
        description="The network endpoint type. For example: <code>unknown</code>, <code>server</code>, <code>desktop</code>, <code>laptop</code>, <code>tablet</code>, <code>mobile</code>, <code>virtual</code>, <code>browser</code>, or <code>other</code>.",
    )
    type_id: TypeId | None = Field(default=None, description="The network endpoint type ID.")
    uid: str | None = Field(default=None, description="The unique identifier of the endpoint.")
    vlan_uid: str | None = Field(default=None, description="The Virtual LAN identifier.")
    vpc_uid: str | None = Field(
        default=None, description="The unique identifier of the Virtual Private Cloud (VPC)."
    )
    zone: str | None = Field(default=None, description="The network zone or LAN segment.")
