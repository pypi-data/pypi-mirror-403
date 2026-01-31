"""Operating System (OS) object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_0_0.enums.type_id import TypeId


class Os(OCSFBaseModel):
    """The Operating System (OS) object describes characteristics of an OS, such as Linux or Windows. Defined by D3FEND <a target='_blank' href='https://d3fend.mitre.org/dao/artifact/d3f:OperatingSystem/'>d3f:OperatingSystem</a>.

    See: https://schema.ocsf.io/1.0.0/objects/os
    """

    name: str = Field(..., description="The operating system name.")
    type_id: TypeId = Field(..., description="The type identifier of the operating system.")
    build: str | None = Field(default=None, description="The operating system build number.")
    country: str | None = Field(
        default=None,
        description="The operating system country code, as defined by the ISO 3166-1 standard (Alpha-2 code). For the complete list of country codes, see <a target='_blank' href='https://www.iso.org/obp/ui/#iso:pub:PUB500001:en'>ISO 3166-1 alpha-2 codes</a>.",
    )
    cpu_bits: int | None = Field(
        default=None,
        description="The cpu architecture, the number of bits used for addressing in memory. For example: <code>32</code> or <code>64</code>.",
    )
    edition: str | None = Field(
        default=None,
        description="The operating system edition. For example: <code>Professional</code>.",
    )
    lang: str | None = Field(
        default=None,
        description="The two letter lower case language codes, as defined by <a target='_blank' href='https://en.wikipedia.org/wiki/ISO_639-1'>ISO 639-1</a>. For example: <code>en</code> (English), <code>de</code> (German), or <code>fr</code> (French).",
    )
    sp_name: str | None = Field(default=None, description="The name of the latest Service Pack.")
    sp_ver: int | None = Field(
        default=None, description="The version number of the latest Service Pack."
    )
    type_: str | None = Field(default=None, description="The type of the operating system.")
    version: str | None = Field(
        default=None,
        description='The version of the OS running on the device that originated the event. For example: "Windows 10", "OS X 10.7", or "iOS 9".',
    )
