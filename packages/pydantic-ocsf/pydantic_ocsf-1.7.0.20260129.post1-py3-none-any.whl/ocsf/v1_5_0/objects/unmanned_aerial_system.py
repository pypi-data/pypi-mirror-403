"""Unmanned Aerial System object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.type_id import TypeId
    from ocsf.v1_5_0.objects.device_hw_info import DeviceHwInfo
    from ocsf.v1_5_0.objects.location import Location


class UnmannedAerialSystem(OCSFBaseModel):
    """The Unmanned Aerial System object describes the characteristics, Position Location Information (PLI), and other metadata of Unmanned Aerial Systems (UAS) and other unmanned and drone systems used in Remote ID. Remote ID is defined in the Standard Specification for Remote ID and Tracking (ASTM Designation: F3411-22a) <a target='_blank' href='https://cdn.standards.iteh.ai/samples/112830/71297057ac42432880a203654f213709/ASTM-F3411-22a.pdf'>ASTM F3411-22a</a>.

    See: https://schema.ocsf.io/1.5.0/objects/unmanned_aerial_system
    """

    hw_info: DeviceHwInfo | None = Field(
        default=None, description="The endpoint hardware information."
    )
    location: Location | None = Field(
        default=None,
        description="The detailed geographical location usually associated with an IP address. [Recommended]",
    )
    model: str | None = Field(
        default=None, description="The model name of the aircraft or unmanned system."
    )
    name: str | None = Field(
        default=None,
        description="The name of the unmanned system as reported by tracking or sensing hardware.",
    )
    serial_number: str | None = Field(
        default=None,
        description="The serial number of the unmanned system. This is expressed in <code>CTA-2063-A</code> format. [Recommended]",
    )
    speed: str | None = Field(
        default=None,
        description="Ground speed of flight. This value is provided in meters per second with a minimum resolution of 0.25 m/s. Special Values: <code>Invalid</code>, <code>No Value</code>, or <code>Unknown: 255 m/s</code>.",
    )
    speed_accuracy: str | None = Field(
        default=None,
        description="Provides quality/containment on horizontal ground speed. Measured in meters/second.",
    )
    track_direction: str | None = Field(
        default=None,
        description="Direction of flight expressed as a “True North-based” ground track angle. This value is provided in clockwise degrees with a minimum resolution of 1 degree. If aircraft is not moving horizontally, use the “Unknown” value",
    )
    type_: str | None = Field(
        default=None,
        description="The type of the UAS. For example, Helicopter, Gyroplane, Rocket, etc.",
    )
    type_id: TypeId | None = Field(
        default=None, description="The UAS type identifier. [Recommended]"
    )
    uid: str | None = Field(
        default=None,
        description="The primary identification identifier for an unmanned system. This can be a Serial Number (in <code>CTA-2063-A</code> format, the Registration ID (provided by the <code>CAA</code>, a UTM, or a unique Session ID. [Recommended]",
    )
    uid_alt: str | None = Field(
        default=None,
        description="A secondary identification identifier for an unmanned system. This can be a Serial Number (in <code>CTA-2063-A</code> format, the Registration ID (provided by the <code>CAA</code>, a UTM, or a unique Session ID. [Recommended]",
    )
    uuid: Any | None = Field(
        default=None,
        description="The Unmanned Aircraft System Traffic Management (UTM) provided universal unique ID (UUID) traceable to a non-obfuscated ID where this UTM UUID acts as a 'session id' to protect exposure of operationally sensitive information. [Recommended]",
    )
    vertical_speed: str | None = Field(
        default=None,
        description="Vertical speed upward relative to the WGS-84 datum, measured in meters per second. Special Values: <code>Invalid</code>, <code>No Value</code>, or <code>Unknown: 63 m/s</code>.",
    )
