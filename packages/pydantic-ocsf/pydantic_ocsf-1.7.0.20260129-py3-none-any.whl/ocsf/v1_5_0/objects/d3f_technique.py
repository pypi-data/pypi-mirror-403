"""MITRE D3FEND™ Technique object."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ocsf._base import OCSFBaseModel


class D3fTechnique(OCSFBaseModel):
    """The MITRE D3FEND™ Technique object describes the leaf defensive technique ID and/or name associated to a countermeasure.

    See: https://schema.ocsf.io/1.5.0/objects/d3f_technique
    """

    name: str | None = Field(
        default=None,
        description="The name of the defensive technique. For example: <code>IO Port Restriction</code>.",
    )
    src_url: Any | None = Field(
        default=None,
        description="The versioned permalink of the defensive technique. For example: <code>https://d3fend.mitre.org/technique/d3f:IOPortRestriction/</code>.",
    )
    uid: str | None = Field(
        default=None,
        description="The unique identifier of the defensive technique. For example: <code>D3-IOPR</code>.",
    )
