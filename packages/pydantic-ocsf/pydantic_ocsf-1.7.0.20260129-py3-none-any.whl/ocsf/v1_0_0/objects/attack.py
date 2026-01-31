"""Attack object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_0_0.objects.tactic import Tactic
    from ocsf.v1_0_0.objects.technique import Technique


class Attack(OCSFBaseModel):
    """The Attack object describes the technique and associated tactics related to an attack. See <a target='_blank' href='https://attack.mitre.org'>MITRE ATT&CK®</a>.

    See: https://schema.ocsf.io/1.0.0/objects/attack
    """

    tactics: list[Tactic] = Field(
        ...,
        description="The a list of tactic ID's/names that are associated with the attack technique, as defined by <a target='_blank' href='https://attack.mitre.org/wiki/ATT&CK_Matrix'>ATT&CK Matrix<sup>TM</sup></a>.",
    )
    technique: Technique = Field(..., description="The attack technique.")
    version: str = Field(..., description="The ATT&CK Matrix version.")
