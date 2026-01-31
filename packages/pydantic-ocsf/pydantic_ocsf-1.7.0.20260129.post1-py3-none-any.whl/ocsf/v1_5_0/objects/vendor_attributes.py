"""Vendor Attributes object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.severity_id import SeverityId


class VendorAttributes(OCSFBaseModel):
    """The Vendor Attributes object can be used to represent values of attributes populated by the Vendor/Finding Provider. It can help distinguish between the vendor-prodvided values and consumer-updated values, of key attributes like <code>severity_id</code>.<br>The original finding producer should not populate this object. It should be populated by consuming systems that support data mutability.

    See: https://schema.ocsf.io/1.5.0/objects/vendor_attributes
    """

    severity: str | None = Field(
        default=None,
        description="The finding severity, as reported by the Vendor (Finding Provider). The value should be normalized to the caption of the <code>severity_id</code> value. In the case of 'Other', it is defined by the source.",
    )
    severity_id: SeverityId | None = Field(
        default=None,
        description="The finding severity ID, as reported by the Vendor (Finding Provider).",
    )
