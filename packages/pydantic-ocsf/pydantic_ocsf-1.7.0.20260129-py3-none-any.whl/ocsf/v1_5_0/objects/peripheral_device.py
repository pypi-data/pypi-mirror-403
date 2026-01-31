"""Peripheral Device object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class PeripheralDevice(OCSFBaseModel):
    """The peripheral device object describes the identity, vendor and model of a peripheral device.

    See: https://schema.ocsf.io/1.5.0/objects/peripheral_device
    """

    class_: str = Field(..., description="The class of the peripheral device.")
    name: str = Field(..., description="The name of the peripheral device.")
    model: str | None = Field(
        default=None, description="The peripheral device model. [Recommended]"
    )
    serial_number: str | None = Field(
        default=None, description="The peripheral device serial number. [Recommended]"
    )
    uid: str | None = Field(
        default=None, description="The unique identifier of the peripheral device. [Recommended]"
    )
    vendor_name: str | None = Field(
        default=None, description="The peripheral device vendor. [Recommended]"
    )
