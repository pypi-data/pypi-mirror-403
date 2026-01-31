"""Endpoint object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.enums.type_id import TypeId
    from ocsf.v1_7_0.objects.agent import Agent
    from ocsf.v1_7_0.objects.device_hw_info import DeviceHwInfo
    from ocsf.v1_7_0.objects.location import Location
    from ocsf.v1_7_0.objects.os import Os
    from ocsf.v1_7_0.objects.user import User


class Endpoint(OCSFBaseModel):
    """The Endpoint object describes a physical or virtual device that connects to and exchanges information with a computer network. Some examples of endpoints are mobile devices, desktop computers, virtual machines, embedded devices, and servers. Internet-of-Things devices—like cameras, lighting, refrigerators, security systems, smart speakers, and thermostats—are also endpoints.

    See: https://schema.ocsf.io/1.7.0/objects/endpoint
    """

    agent_list: list[Agent] | None = Field(
        default=None,
        description="A list of <code>agent</code> objects associated with a device, endpoint, or resource.",
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
    os: Os | None = Field(default=None, description="The endpoint operating system.")
    owner: User | None = Field(
        default=None,
        description="The identity of the service or user account that owns the endpoint or was last logged into it. [Recommended]",
    )
    subnet_uid: str | None = Field(
        default=None, description="The unique identifier of a virtual subnet."
    )
    type_: str | None = Field(
        default=None,
        description="The endpoint type. For example: <code>unknown</code>, <code>server</code>, <code>desktop</code>, <code>laptop</code>, <code>tablet</code>, <code>mobile</code>, <code>virtual</code>, <code>browser</code>, or <code>other</code>.",
    )
    type_id: TypeId | None = Field(default=None, description="The endpoint type ID. [Recommended]")
    uid: str | None = Field(default=None, description="The unique identifier of the endpoint.")
    vlan_uid: str | None = Field(default=None, description="The Virtual LAN identifier.")
    vpc_uid: str | None = Field(
        default=None, description="The unique identifier of the Virtual Private Cloud (VPC)."
    )
    zone: str | None = Field(default=None, description="The network zone or LAN segment.")
