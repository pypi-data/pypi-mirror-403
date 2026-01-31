"""Geo Location object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Location(OCSFBaseModel):
    """The Geo Location object describes a geographical location, usually associated with an IP address. Defined by D3FEND <a target='_blank' href='https://d3fend.mitre.org/dao/artifact/d3f:PhysicalLocation/'>d3f:PhysicalLocation</a>.

    See: https://schema.ocsf.io/1.1.0/objects/location
    """

    city: str | None = Field(default=None, description="The name of the city. [Recommended]")
    continent: str | None = Field(
        default=None, description="The name of the continent. [Recommended]"
    )
    coordinates: list[float] | None = Field(
        default=None,
        description="A two-element array, containing a longitude/latitude pair. The format conforms with <a target='_blank' href='https://geojson.org'>GeoJSON</a>. For example: <code>[-73.983, 40.719]</code>. [Recommended]",
    )
    country: str | None = Field(
        default=None,
        description="The ISO 3166-1 Alpha-2 country code. For the complete list of country codes see <a target='_blank' href='https://www.iso.org/obp/ui/#iso:pub:PUB500001:en' >ISO 3166-1 alpha-2 codes</a>.<p><b>Note:</b> The two letter country code should be capitalized. For example: <code>US</code> or <code>CA</code>.</p> [Recommended]",
    )
    desc: str | None = Field(
        default=None, description="The description of the geographical location."
    )
    is_on_premises: bool | None = Field(
        default=None, description="The indication of whether the location is on premises."
    )
    isp: str | None = Field(
        default=None, description="The name of the Internet Service Provider (ISP)."
    )
    postal_code: str | None = Field(default=None, description="The postal code of the location.")
    provider: str | None = Field(
        default=None, description="The provider of the geographical location data."
    )
    region: str | None = Field(
        default=None,
        description="The alphanumeric code that identifies the principal subdivision (e.g. province or state) of the country. Region codes are defined at <a target='_blank' href='https://www.iso.org/iso-3166-country-codes.html'>ISO 3166-2</a> and have a limit of three characters. For example, see <a target='_blank' href='https://www.iso.org/obp/ui/#iso:code:3166:US'>the region codes for the US</a>.",
    )
