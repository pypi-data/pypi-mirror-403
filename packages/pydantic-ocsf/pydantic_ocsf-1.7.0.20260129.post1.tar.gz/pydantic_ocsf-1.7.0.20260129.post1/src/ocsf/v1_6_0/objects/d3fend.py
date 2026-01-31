"""MITRE D3FEND™ object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.objects.d3f_tactic import D3fTactic
    from ocsf.v1_6_0.objects.d3f_technique import D3fTechnique


class D3fend(OCSFBaseModel):
    """The MITRE D3FEND™ object describes the tactic & technique associated with a countermeasure.

    See: https://schema.ocsf.io/1.6.0/objects/d3fend
    """

    d3f_tactic: D3fTactic | None = Field(
        default=None,
        description="The Tactic object describes the tactic ID and/or name that is associated with a countermeasure. [Recommended]",
    )
    d3f_technique: D3fTechnique | None = Field(
        default=None,
        description="The Technique object describes the technique ID and/or name associated with a countermeasure. [Recommended]",
    )
    version: str | None = Field(
        default=None, description="The D3FEND™ Matrix version. [Recommended]"
    )
