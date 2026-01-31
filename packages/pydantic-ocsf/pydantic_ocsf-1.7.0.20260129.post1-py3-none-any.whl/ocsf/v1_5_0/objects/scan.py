"""Scan object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.type_id import TypeId


class Scan(OCSFBaseModel):
    """The Scan object describes characteristics of a proactive scan.

    See: https://schema.ocsf.io/1.5.0/objects/scan
    """

    type_id: TypeId = Field(..., description="The type id of the scan.")
    name: str | None = Field(
        default=None,
        description='The administrator-supplied or application-generated name of the scan. For example: "Home office weekly user database scan", "Scan folders for viruses", "Full system virus scan"',
    )
    type_: str | None = Field(default=None, description="The type of scan.")
    uid: str | None = Field(
        default=None,
        description="The application-defined unique identifier assigned to an instance of a scan.",
    )
