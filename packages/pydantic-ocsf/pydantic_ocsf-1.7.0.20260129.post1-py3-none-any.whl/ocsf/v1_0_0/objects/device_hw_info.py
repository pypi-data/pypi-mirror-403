"""Device Hardware Info object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_0_0.objects.display import Display
    from ocsf.v1_0_0.objects.keyboard_info import KeyboardInfo


class DeviceHwInfo(OCSFBaseModel):
    """The Device Hardware Information object contains details and specifications of the physical components that make up a device. This information provides an overview of the hardware capabilities, configuration, and characteristics of the device.

    See: https://schema.ocsf.io/1.0.0/objects/device_hw_info
    """

    bios_date: str | None = Field(
        default=None, description="The BIOS date. For example: <code>03/31/16</code>."
    )
    bios_manufacturer: str | None = Field(
        default=None, description="The BIOS manufacturer. For example: <code>LENOVO</code>."
    )
    bios_ver: str | None = Field(
        default=None,
        description="The BIOS version. For example: <code>LENOVO G5ETA2WW (2.62)</code>.",
    )
    chassis: str | None = Field(
        default=None,
        description="The chassis type describes the system enclosure or physical form factor. Such as the following examples for Windows <a target='_blank' href='https://docs.microsoft.com/en-us/windows/win32/cimwin32prov/win32-systemenclosure'>Windows Chassis Types</a>",
    )
    cpu_bits: int | None = Field(
        default=None,
        description="The cpu architecture, the number of bits used for addressing in memory. For example: <code>32</code> or <code>64</code>.",
    )
    cpu_cores: int | None = Field(
        default=None,
        description="The number of processor cores in all installed processors. For Example: <code>42</code>.",
    )
    cpu_count: int | None = Field(
        default=None,
        description="The number of physical processors on a system. For example: <code>1</code>.",
    )
    cpu_speed: int | None = Field(
        default=None,
        description="The speed of the processor in Mhz. For Example: <code>4200</code>.",
    )
    cpu_type: str | None = Field(
        default=None,
        description="The processor type. For example: <code>x86 Family 6 Model 37 Stepping 5</code>.",
    )
    desktop_display: Display | None = Field(
        default=None, description="The desktop display affiliated with the event"
    )
    keyboard_info: KeyboardInfo | None = Field(
        default=None, description="The keyboard detailed information."
    )
    ram_size: int | None = Field(
        default=None,
        description="The total amount of installed RAM, in Megabytes. For example: <code>2048</code>.",
    )
    serial_number: str | None = Field(
        default=None, description="The device manufacturer serial number."
    )
