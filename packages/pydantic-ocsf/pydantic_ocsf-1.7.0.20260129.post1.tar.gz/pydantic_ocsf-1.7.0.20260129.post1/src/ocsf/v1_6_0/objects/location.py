"""Geo Location object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Location(OCSFBaseModel):
    """The Geo Location object describes a geographical location, usually associated with an IP address.

    See: https://schema.ocsf.io/1.6.0/objects/location
    """

    aerial_height: str | None = Field(
        default=None,
        description="Expressed as either height above takeoff location or height above ground level (AGL) for a UAS current location. This value is provided in meters and must have a minimum resolution of 1 m. Special Values: <code>Invalid</code>, <code>No Value</code>, or <code>Unknown: -1000 m</code>.",
    )
    city: str | None = Field(default=None, description="The name of the city. [Recommended]")
    continent: str | None = Field(
        default=None, description="The name of the continent. [Recommended]"
    )
    coordinates: list[float] | None = Field(
        default=None,
        description="A two-element array, containing a longitude/latitude pair. The format conforms with <a target='_blank' href='https://geojson.org'>GeoJSON</a>. For example: <code>[-73.983, 40.719]</code>.",
    )
    country: str | None = Field(
        default=None,
        description="The ISO 3166-1 Alpha-2 country code.<p><b>Note:</b> The two letter country code should be capitalized. For example: <code>US</code> or <code>CA</code>.</p> [Recommended]",
    )
    desc: str | None = Field(
        default=None, description="The description of the geographical location."
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
    region: str | None = Field(
        default=None,
        description="The alphanumeric code that identifies the principal subdivision (e.g. province or state) of the country. For example, 'CH-VD' for the Canton of Vaud, Switzerland",
    )
