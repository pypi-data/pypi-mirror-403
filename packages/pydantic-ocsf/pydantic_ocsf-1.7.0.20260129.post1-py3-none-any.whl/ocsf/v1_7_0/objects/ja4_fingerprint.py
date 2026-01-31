"""JA4+ Fingerprint object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.enums.type_id import TypeId


class Ja4Fingerprint(OCSFBaseModel):
    """The JA4+ fingerprint object provides detailed fingerprint information about various aspects of network traffic which is both machine and human readable.

    See: https://schema.ocsf.io/1.7.0/objects/ja4_fingerprint
    """

    type_id: TypeId = Field(..., description="The identifier of the JA4+ fingerprint type.")
    value: str = Field(..., description="The JA4+ fingerprint value.")
    section_a: str | None = Field(
        default=None, description="The 'a' section of the JA4 fingerprint."
    )
    section_b: str | None = Field(
        default=None, description="The 'b' section of the JA4 fingerprint."
    )
    section_c: str | None = Field(
        default=None, description="The 'c' section of the JA4 fingerprint."
    )
    section_d: str | None = Field(
        default=None, description="The 'd' section of the JA4 fingerprint."
    )
    type_: str | None = Field(
        default=None,
        description="The JA4+ fingerprint type as defined by <a href='https://blog.foxio.io/ja4+-network-fingerprinting target='_blank'>FoxIO</a>, normalized to the caption of 'type_id'. In the case of 'Other', it is defined by the event source.",
    )
