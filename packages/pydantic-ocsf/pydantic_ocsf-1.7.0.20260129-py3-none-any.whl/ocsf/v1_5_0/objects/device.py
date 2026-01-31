"""Device object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.risk_level_id import RiskLevelId
    from ocsf.v1_5_0.enums.type_id import TypeId
    from ocsf.v1_5_0.objects.agent import Agent
    from ocsf.v1_5_0.objects.device_hw_info import DeviceHwInfo
    from ocsf.v1_5_0.objects.group import Group
    from ocsf.v1_5_0.objects.image import Image
    from ocsf.v1_5_0.objects.location import Location
    from ocsf.v1_5_0.objects.network_interface import NetworkInterface
    from ocsf.v1_5_0.objects.organization import Organization
    from ocsf.v1_5_0.objects.os import Os
    from ocsf.v1_5_0.objects.user import User


class Device(OCSFBaseModel):
    """The Device object represents an addressable computer system or host, which is typically connected to a computer network and participates in the transmission or processing of data within the computer network.

    See: https://schema.ocsf.io/1.5.0/objects/device
    """

    type_id: TypeId = Field(..., description="The device type ID.")
    agent_list: list[Agent] | None = Field(
        default=None,
        description="A list of <code>agent</code> objects associated with a device, endpoint, or resource.",
    )
    autoscale_uid: str | None = Field(
        default=None, description="The unique identifier of the cloud autoscale configuration."
    )
    boot_time: int | None = Field(default=None, description="The time the system was booted.")
    boot_uid: str | None = Field(
        default=None,
        description="A unique identifier of the device that changes after every reboot. For example, the value of <code>/proc/sys/kernel/random/boot_id</code> from Linux's procfs.",
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
    eid: str | None = Field(
        default=None,
        description="An Embedded Identity Document, is a unique serial number that identifies an eSIM-enabled device.",
    )
    first_seen_time: int | None = Field(
        default=None, description="The initial discovery time of the device."
    )
    groups: list[Group] | None = Field(
        default=None,
        description='The group names to which the device belongs. For example: <code>["Windows Laptops", "Engineering"]</code>.',
    )
    hostname: Any | None = Field(default=None, description="The device hostname. [Recommended]")
    hw_info: DeviceHwInfo | None = Field(
        default=None, description="The endpoint hardware information."
    )
    hypervisor: str | None = Field(
        default=None,
        description="The name of the hypervisor running on the device. For example, <code>Xen</code>, <code>VMware</code>, <code>Hyper-V</code>, <code>VirtualBox</code>, etc.",
    )
    iccid: str | None = Field(
        default=None,
        description="The Integrated Circuit Card Identification of a mobile device. Typically it is a unique 18 to 22 digit number that identifies a SIM card.",
    )
    image: Image | None = Field(
        default=None, description="The image used as a template to run the virtual machine."
    )
    imei: str | None = Field(
        default=None,
        description="The International Mobile Equipment Identity that is associated with the device.",
    )
    imei_list: list[str] | None = Field(
        default=None,
        description="The International Mobile Equipment Identity values that are associated with the device.",
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
        default=None, description="The device IP address, in either IPv4 or IPv6 format."
    )
    is_backed_up: bool | None = Field(
        default=None,
        description="Indicates whether the device or resource has a backup enabled, such as an automated snapshot or a cloud backup. For example, this is indicated by the <code>cloudBackupEnabled</code> value within JAMF Pro mobile devices or the registration of an AWS ARN with the AWS Backup service.",
    )
    is_compliant: bool | None = Field(
        default=None, description="The event occurred on a compliant device."
    )
    is_managed: bool | None = Field(
        default=None, description="The event occurred on a managed device."
    )
    is_mobile_account_active: bool | None = Field(
        default=None,
        description="Indicates whether the device has an active mobile account. For example, this is indicated by the <code>itunesStoreAccountActive</code> value within JAMF Pro mobile devices.",
    )
    is_personal: bool | None = Field(
        default=None, description="The event occurred on a personal device."
    )
    is_shared: bool | None = Field(
        default=None, description="The event occurred on a shared device."
    )
    is_supervised: bool | None = Field(
        default=None,
        description="The event occurred on a supervised device. Devices that are supervised are typically mobile devices managed by a Mobile Device Management solution and are restricted from specific behaviors such as Apple AirDrop.",
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
        default=None, description="The Media Access Control (MAC) address of the endpoint."
    )
    meid: str | None = Field(
        default=None,
        description="The Mobile Equipment Identifier. It's a unique number that identifies a Code Division Multiple Access (CDMA) mobile device.",
    )
    model: str | None = Field(
        default=None,
        description="The model of the device. For example <code>ThinkPad X1 Carbon</code>.",
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
        description="The physical or virtual network interfaces that are associated with the device, one for each unique MAC address/IP address/hostname/name combination.<p><b>Note:</b> The first element of the array is the network information that pertains to the event.</p>",
    )
    org: Organization | None = Field(
        default=None, description="Organization and org unit related to the device."
    )
    os: Os | None = Field(default=None, description="The endpoint operating system.")
    os_machine_uuid: Any | None = Field(
        default=None,
        description="The operating system assigned Machine ID. In Windows, this is the value stored at the registry path: <code>HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Cryptography\\MachineGuid</code>. In Linux, this is stored in the file: <code>/etc/machine-id</code>.",
    )
    owner: User | None = Field(
        default=None,
        description="The identity of the service or user account that owns the endpoint or was last logged into it. [Recommended]",
    )
    region: str | None = Field(
        default=None,
        description="The region where the virtual machine is located. For example, an AWS Region. [Recommended]",
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
    subnet: Any | None = Field(default=None, description="The subnet mask.")
    subnet_uid: str | None = Field(
        default=None, description="The unique identifier of a virtual subnet."
    )
    type_: str | None = Field(
        default=None,
        description="The device type. For example: <code>unknown</code>, <code>server</code>, <code>desktop</code>, <code>laptop</code>, <code>tablet</code>, <code>mobile</code>, <code>virtual</code>, <code>browser</code>, or <code>other</code>. [Recommended]",
    )
    udid: str | None = Field(
        default=None,
        description="The Apple assigned Unique Device Identifier (UDID). For iOS, iPadOS, tvOS, watchOS and visionOS devices, this is the UDID. For macOS devices, it is the Provisioning UDID. For example: <code>00008020-008D4548007B4F26</code>",
    )
    uid: str | None = Field(
        default=None,
        description="The unique identifier of the device. For example the Windows TargetSID or AWS EC2 ARN. [Recommended]",
    )
    uid_alt: str | None = Field(
        default=None,
        description="An alternate unique identifier of the device if any. For example the ActiveDirectory DN.",
    )
    vendor_name: str | None = Field(
        default=None,
        description="The vendor for the device. For example <code>Dell</code> or <code>Lenovo</code>. [Recommended]",
    )
    vlan_uid: str | None = Field(default=None, description="The Virtual LAN identifier.")
    vpc_uid: str | None = Field(
        default=None, description="The unique identifier of the Virtual Private Cloud (VPC)."
    )
    zone: str | None = Field(default=None, description="The network zone or LAN segment.")
