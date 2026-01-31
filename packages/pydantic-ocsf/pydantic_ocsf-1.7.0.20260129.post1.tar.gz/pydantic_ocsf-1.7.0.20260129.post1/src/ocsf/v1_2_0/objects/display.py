"""Display object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Display(OCSFBaseModel):
    """The Display object contains information about the physical or virtual display connected to a computer system.

    See: https://schema.ocsf.io/1.2.0/objects/display
    """

    color_depth: int | None = Field(default=None, description="The numeric color depth.")
    physical_height: int | None = Field(
        default=None, description="The numeric physical height of display."
    )
    physical_orientation: int | None = Field(
        default=None, description="The numeric physical orientation of display."
    )
    physical_width: int | None = Field(
        default=None, description="The numeric physical width of display."
    )
    scale_factor: int | None = Field(
        default=None, description="The numeric scale factor of display."
    )
