"""Peripheral Device object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.enums.type_id import TypeId


class PeripheralDevice(OCSFBaseModel):
    """The peripheral device object describes the properties of external, connectable, and detachable hardware.

    See: https://schema.ocsf.io/1.7.0/objects/peripheral_device
    """

    name: str = Field(..., description="The name of the peripheral device.")
    class_: str | None = Field(default=None, description="The class of the peripheral device.")
    model: str | None = Field(
        default=None, description="The peripheral device model. [Recommended]"
    )
    serial_number: str | None = Field(
        default=None, description="The peripheral device serial number. [Recommended]"
    )
    type_: str | None = Field(
        default=None,
        description="The Peripheral Device type, normalized to the caption of the <code>type_id</code> value. In the case of 'Other', it is defined by the source.",
    )
    type_id: TypeId | None = Field(
        default=None, description="The normalized peripheral device type ID. [Recommended]"
    )
    uid: str | None = Field(
        default=None, description="The unique identifier of the peripheral device. [Recommended]"
    )
    vendor_id_list: list[str] | None = Field(
        default=None, description="The list of vendor IDs for the peripheral device. [Recommended]"
    )
    vendor_name: str | None = Field(
        default=None, description="The primary vendor name for the peripheral device. [Recommended]"
    )
