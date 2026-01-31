"""Device object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_0_0.enums.risk_level_id import RiskLevelId
    from ocsf.v1_0_0.enums.type_id import TypeId
    from ocsf.v1_0_0.objects.device_hw_info import DeviceHwInfo
    from ocsf.v1_0_0.objects.group import Group
    from ocsf.v1_0_0.objects.image import Image
    from ocsf.v1_0_0.objects.location import Location
    from ocsf.v1_0_0.objects.network_interface import NetworkInterface
    from ocsf.v1_0_0.objects.organization import Organization
    from ocsf.v1_0_0.objects.os import Os


class Device(OCSFBaseModel):
    """The Device object represents an addressable computer system or host, which is typically connected to a computer network and participates in the transmission or processing of data within the computer network. Defined by D3FEND <a target='_blank' href='https://d3fend.mitre.org/dao/artifact/d3f:Host/'>d3f:Host</a>.

    See: https://schema.ocsf.io/1.0.0/objects/device
    """

    type_id: TypeId = Field(..., description="The device type ID.")
    autoscale_uid: str | None = Field(
        default=None, description="The unique identifier of the cloud autoscale configuration."
    )
    created_time: int | None = Field(
        default=None, description="The time when the device was known to have been created."
    )
    desc: str | None = Field(
        default=None,
        description="The description of the device, ordinarily as reported by the operating system.",
    )
    domain: str | None = Field(
        default=None,
        description="The network domain where the device resides. For example: <code>work.example.com</code>.",
    )
    first_seen_time: int | None = Field(
        default=None, description="The initial discovery time of the device."
    )
    groups: list[Group] | None = Field(
        default=None,
        description='The group names to which the device belongs. For example: <code>["Windows Laptops", "Engineering"]<code/>.',
    )
    hostname: Any | None = Field(default=None, description="The device hostname.")
    hw_info: DeviceHwInfo | None = Field(
        default=None, description="The device hardware information."
    )
    hypervisor: str | None = Field(
        default=None,
        description="The name of the hypervisor running on the device. For example, <code>Xen</code>, <code>VMware</code>, <code>Hyper-V</code>, <code>VirtualBox</code>, etc.",
    )
    image: Image | None = Field(
        default=None, description="The image used as a template to run the virtual machine."
    )
    imei: str | None = Field(
        default=None,
        description="The International Mobile Station Equipment Identifier that is associated with the device.",
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
    ip: Any | None = Field(
        default=None, description="The device IP address, in either IPv4 or IPv6 format."
    )
    is_compliant: bool | None = Field(
        default=None, description="The event occurred on a compliant device."
    )
    is_managed: bool | None = Field(
        default=None, description="The event occurred on a managed device."
    )
    is_personal: bool | None = Field(
        default=None, description="The event occurred on a personal device."
    )
    is_trusted: bool | None = Field(
        default=None, description="The event occurred on a trusted device."
    )
    last_seen_time: int | None = Field(
        default=None, description="The most recent discovery time of the device."
    )
    location: Location | None = Field(
        default=None, description="The geographical location of the device."
    )
    mac: Any | None = Field(
        default=None, description="The device Media Access Control (MAC) address."
    )
    modified_time: int | None = Field(
        default=None, description="The time when the device was last known to have been modified."
    )
    name: str | None = Field(
        default=None,
        description="The alternate device name, ordinarily as assigned by an administrator. <p><b>Note:</b> The <b>Name</b> could be any other string that helps to identify the device, such as a phone number; for example <code>310-555-1234</code>.</p>",
    )
    network_interfaces: list[NetworkInterface] | None = Field(
        default=None,
        description="The network interfaces that are associated with the device, one for each unique MAC address/IP address/hostname/name combination.<p><b>Note:</b> The first element of the array is the network information that pertains to the event.</p>",
    )
    org: Organization | None = Field(
        default=None, description="Organization and org unit related to the device."
    )
    os: Os | None = Field(default=None, description="The device operating system.")
    region: str | None = Field(
        default=None,
        description="The region where the virtual machine is located. For example, an AWS Region. [Recommended]",
    )
    risk_level: str | None = Field(
        default=None,
        description="The risk level, normalized to the caption of the risk_level_id value. In the case of 'Other', it is defined by the event source.",
    )
    risk_level_id: RiskLevelId | None = Field(
        default=None, description="The normalized risk level id."
    )
    risk_score: int | None = Field(
        default=None, description="The risk score as reported by the event source."
    )
    subnet: Any | None = Field(default=None, description="The subnet mask.")
    subnet_uid: str | None = Field(
        default=None, description="The unique identifier of a virtual subnet."
    )
    type_: str | None = Field(
        default=None,
        description="The device type. For example: <code>unknown</code>, <code>server</code>, <code>desktop</code>, <code>laptop</code>, <code>tablet</code>, <code>mobile</code>, <code>virtual</code>, <code>browser</code>, or <code>other</code>.",
    )
    uid: str | None = Field(
        default=None,
        description="The unique identifier of the device. For example the Windows TargetSID or AWS EC2 ARN.",
    )
    uid_alt: str | None = Field(
        default=None,
        description="An alternate unique identifier of the device if any. For example the ActiveDirectory DN.",
    )
    vlan_uid: str | None = Field(default=None, description="The Virtual LAN identifier.")
    vpc_uid: str | None = Field(
        default=None, description="The unique identifier of the Virtual Private Cloud (VPC)."
    )
