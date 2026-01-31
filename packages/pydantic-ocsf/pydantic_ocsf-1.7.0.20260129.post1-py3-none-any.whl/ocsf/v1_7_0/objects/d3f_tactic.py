"""MITRE D3FEND™ Tactic object."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ocsf._base import OCSFBaseModel


class D3fTactic(OCSFBaseModel):
    """The MITRE D3FEND™ Tactic object describes the tactic ID and/or name that is associated to an attack.

    See: https://schema.ocsf.io/1.7.0/objects/d3f_tactic
    """

    name: str | None = Field(
        default=None,
        description="The tactic name that is associated with the defensive technique. For example: <code>Isolate</code>.",
    )
    src_url: Any | None = Field(
        default=None,
        description="The versioned permalink of the defensive tactic. For example: <code>https://d3fend.mitre.org/tactic/d3f:Isolate/</code>.",
    )
    uid: str | None = Field(
        default=None, description="The unique identifier of the defensive tactic."
    )
