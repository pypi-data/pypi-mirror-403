"""Network Endpoint object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_0_0.objects.location import Location


class NetworkEndpoint(OCSFBaseModel):
    """The Network Endpoint object describes characteristics of a network endpoint. These can be a source or destination of a network connection.

    See: https://schema.ocsf.io/1.0.0/objects/network_endpoint
    """

    domain: str | None = Field(default=None, description="The name of the domain.")
    hostname: Any | None = Field(
        default=None, description="The fully qualified name of the endpoint. [Recommended]"
    )
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
    location: Location | None = Field(
        default=None, description="The geographical location of the endpoint."
    )
    mac: Any | None = Field(
        default=None, description="The Media Access Control (MAC) address of the endpoint."
    )
    name: str | None = Field(default=None, description="The short name of the endpoint.")
    port: Any | None = Field(
        default=None,
        description="The port used for communication within the network connection. [Recommended]",
    )
    subnet_uid: str | None = Field(
        default=None, description="The unique identifier of a virtual subnet."
    )
    svc_name: str | None = Field(
        default=None,
        description="The service name in service-to-service connections. For example, AWS VPC logs the pkt-src-aws-service and pkt-dst-aws-service fields identify the connection is coming from or going to an AWS service. [Recommended]",
    )
    uid: str | None = Field(default=None, description="The unique identifier of the endpoint.")
    vlan_uid: str | None = Field(default=None, description="The Virtual LAN identifier.")
    vpc_uid: str | None = Field(
        default=None, description="The unique identifier of the Virtual Private Cloud (VPC)."
    )
