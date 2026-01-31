"""Aircraft object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.objects.location import Location


class Aircraft(OCSFBaseModel):
    """The Aircraft object represents any aircraft or otherwise airborne asset such as an unmanned system, airplane, balloon, spacecraft, or otherwise. The Aircraft object is intended to normalized data captured or otherwise logged from active radar, passive radar, multi-spectral systems, or the Automatic Dependant Broadcast - Surveillance (ADS-B), and/or Mode S systems.

    See: https://schema.ocsf.io/1.5.0/objects/aircraft
    """

    location: Location | None = Field(
        default=None,
        description="The detailed geographical location usually associated with an IP address. [Recommended]",
    )
    model: str | None = Field(
        default=None, description="The model name of the aircraft or unmanned system."
    )
    name: str | None = Field(
        default=None,
        description="The name of the aircraft, such as the such as the flight name or callsign. [Recommended]",
    )
    serial_number: str | None = Field(
        default=None, description="The serial number of the aircraft."
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
    uid: str | None = Field(
        default=None,
        description="The primary identification identifier for an aircraft, such as the 24-bit International Civil Aviation Organization (ICAO) identifier of the aircraft, as 6 hex digits. [Recommended]",
    )
    uid_alt: str | None = Field(
        default=None,
        description="A secondary identification identifier for an aircraft, such as the 4-digit squawk (octal representation).",
    )
    vertical_speed: str | None = Field(
        default=None,
        description="Vertical speed upward relative to the WGS-84 datum, measured in meters per second. Special Values: <code>Invalid</code>, <code>No Value</code>, or <code>Unknown: 63 m/s</code>.",
    )
