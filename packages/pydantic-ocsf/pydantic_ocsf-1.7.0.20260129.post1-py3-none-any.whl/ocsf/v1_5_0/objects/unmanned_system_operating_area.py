"""Unmanned System Operating Area object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.type_id import TypeId
    from ocsf.v1_5_0.objects.location import Location


class UnmannedSystemOperatingArea(OCSFBaseModel):
    """The Unmanned System Operating Area object describes details about a precise area of operations for a UAS flight or mission.

    See: https://schema.ocsf.io/1.5.0/objects/unmanned_system_operating_area
    """

    aerial_height: str | None = Field(
        default=None,
        description="Expressed as either height above takeoff location or height above ground level (AGL) for a UAS current location. This value is provided in meters and must have a minimum resolution of 1 m. Special Values: <code>Invalid</code>, <code>No Value</code>, or <code>Unknown: -1000 m</code>.",
    )
    altitude_ceiling: str | None = Field(
        default=None,
        description="Maximum altitude (WGS-84 HAE) for a group or an Intent-Based Network Participant. Measured in meters. Special Values: <code>Invalid</code>, <code>No Value</code>, or <code>Unknown: -1000 m</code>.",
    )
    altitude_floor: str | None = Field(
        default=None,
        description="Minimum altitude (WGS-84 HAE) for a group or an Intent-Based Network Participant. Measured in meters. Special Values: <code>Invalid</code>, <code>No Value</code>, or <code>Unknown: -1000 m</code>.",
    )
    city: str | None = Field(default=None, description="The name of the city. [Recommended]")
    continent: str | None = Field(
        default=None, description="The name of the continent. [Recommended]"
    )
    coordinates: list[float] | None = Field(
        default=None,
        description="A two-element array, containing a longitude/latitude pair. The format conforms with <a target='_blank' href='https://geojson.org'>GeoJSON</a>. For example: <code>[-73.983, 40.719]</code>.",
    )
    count: int | None = Field(
        default=None, description="Indicates the number of UAS in the operating area. [Recommended]"
    )
    country: str | None = Field(
        default=None,
        description="The ISO 3166-1 Alpha-2 country code.<p><b>Note:</b> The two letter country code should be capitalized. For example: <code>US</code> or <code>CA</code>.</p> [Recommended]",
    )
    desc: str | None = Field(
        default=None, description="The description of the geographical location."
    )
    end_time: int | None = Field(
        default=None,
        description="The date and time at which a group or an Intent-Based Network Participant operation ends. (This field is only applicable to Network Remote ID.)",
    )
    geodetic_altitude: str | None = Field(
        default=None,
        description="The aircraft distance above or below the ellipsoid as measured along a line that passes through the aircraft and is normal to the surface of the WGS-84 ellipsoid. This value is provided in meters and must have a minimum resolution of 1 m. Special Values: <code>Invalid</code>, <code>No Value</code>, or <code>Unknown: -1000 m</code>.",
    )
    geodetic_vertical_accuracy: str | None = Field(
        default=None,
        description="Provides quality/containment on geodetic altitude. This is based on ADS-B Geodetic Vertical Accuracy (GVA). Measured in meters.",
    )
    geohash: str | None = Field(
        default=None,
        description="<p>Geohash of the geo-coordinates (latitude and longitude).</p><a target='_blank' href='https://en.wikipedia.org/wiki/Geohash'>Geohashing</a> is a geocoding system used to encode geographic coordinates in decimal degrees, to a single string.",
    )
    horizontal_accuracy: str | None = Field(
        default=None,
        description="Provides quality/containment on horizontal position. This is based on ADS-B NACp. Measured in meters.",
    )
    is_on_premises: bool | None = Field(
        default=None, description="The indication of whether the location is on premises."
    )
    isp: str | None = Field(
        default=None, description="The name of the Internet Service Provider (ISP)."
    )
    lat: float | None = Field(
        default=None,
        description="The geographical Latitude coordinate represented in Decimal Degrees (DD). For example: <code>42.361145</code>.",
    )
    locations: list[Location] | None = Field(
        default=None,
        description="A list of Position Location Information (PLI) (latitude/longitude pairs) defining the area where a group or Intent-Based Network Participant operation is taking place. (This field is only applicable to Network Remote ID.) [Recommended]",
    )
    long: float | None = Field(
        default=None,
        description="The geographical Longitude coordinate represented in Decimal Degrees (DD). For example: <code>-71.057083</code>.",
    )
    postal_code: str | None = Field(default=None, description="The postal code of the location.")
    pressure_altitude: str | None = Field(
        default=None,
        description="The uncorrected barometric pressure altitude (based on reference standard 29.92 inHg, 1013.25 mb) provides a reference for algorithms that utilize 'altitude deltas' between aircraft. This value is provided in meters and must have a minimum resolution of 1 m.. Special Values: <code>Invalid</code>, <code>No Value</code>, or <code>Unknown: -1000 m</code>.",
    )
    provider: str | None = Field(
        default=None, description="The provider of the geographical location data."
    )
    radius: str | None = Field(
        default=None,
        description="Farthest horizontal distance from the reported location at which any UA in a group may be located (meters). Also allows defining the area where an Intent-Based Network Participant operation is taking place. Default: 0 m.",
    )
    region: str | None = Field(
        default=None,
        description="The alphanumeric code that identifies the principal subdivision (e.g. province or state) of the country. For example, 'CH-VD' for the Canton of Vaud, Switzerland",
    )
    start_time: int | None = Field(
        default=None,
        description="The date and time at which a group or an Intent-Based Network Participant operation starts. (This field is only applicable to Network Remote ID.)",
    )
    type_: str | None = Field(
        default=None,
        description="The type of operating area. For example, <code>Takeoff Location</code>, <code>Fixed Location</code>, <code>Dynamic Location</code>.",
    )
    type_id: TypeId | None = Field(
        default=None, description="The operating area type identifier. [Recommended]"
    )
