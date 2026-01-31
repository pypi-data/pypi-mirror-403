"""Keyboard Information object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class KeyboardInfo(OCSFBaseModel):
    """The Keyboard Information object contains details and attributes related to a computer or device keyboard. It encompasses information that describes the characteristics, capabilities, and configuration of the keyboard.

    See: https://schema.ocsf.io/1.7.0/objects/keyboard_info
    """

    function_keys: int | None = Field(
        default=None, description="The number of function keys on client keyboard."
    )
    ime: str | None = Field(default=None, description="The Input Method Editor (IME) file name.")
    keyboard_layout: str | None = Field(
        default=None, description="The keyboard locale identifier name (e.g., en-US)."
    )
    keyboard_subtype: int | None = Field(default=None, description="The keyboard numeric code.")
    keyboard_type: str | None = Field(
        default=None, description="The keyboard type (e.g., xt, ico)."
    )
