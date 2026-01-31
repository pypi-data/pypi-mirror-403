"""MITRE ATT&CK® object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_1_0.objects.sub_technique import SubTechnique
    from ocsf.v1_1_0.objects.tactic import Tactic
    from ocsf.v1_1_0.objects.technique import Technique


class Attack(OCSFBaseModel):
    """The <a target='_blank' href='https://attack.mitre.org'>MITRE ATT&CK®</a> object describes the tactic, technique & sub-technique associated to an attack as defined in <a target='_blank' href='https://attack.mitre.org/wiki/ATT&CK_Matrix'>ATT&CK Matrix<sup>TM</sup></a>.

    See: https://schema.ocsf.io/1.1.0/objects/attack
    """

    sub_technique: SubTechnique | None = Field(
        default=None,
        description="The Sub Technique object describes the sub technique ID and/or name associated to an attack, as defined by <a target='_blank' href='https://attack.mitre.org/wiki/ATT&CK_Matrix'>ATT&CK Matrix<sup>TM</sup></a>.",
    )
    tactic: Tactic | None = Field(
        default=None,
        description="The Tactic object describes the tactic ID and/or name that is associated to an attack, as defined by <a target='_blank' href='https://attack.mitre.org/wiki/ATT&CK_Matrix'>ATT&CK Matrix<sup>TM</sup></a>.",
    )
    tactics: list[Tactic] | None = Field(
        default=None,
        description="The Tactic object describes the tactic ID and/or tactic name that are associated with the attack technique, as defined by <a target='_blank' href='https://attack.mitre.org/wiki/ATT&CK_Matrix'>ATT&CK Matrix<sup>TM</sup></a>.",
    )
    technique: Technique | None = Field(
        default=None,
        description="The Technique object describes the technique ID and/or name associated to an attack, as defined by <a target='_blank' href='https://attack.mitre.org/wiki/ATT&CK_Matrix'>ATT&CK Matrix<sup>TM</sup></a>.",
    )
    version: str | None = Field(
        default=None,
        description="The <a target='_blank' href='https://attack.mitre.org/wiki/ATT&CK_Matrix'>ATT&CK Matrix<sup>TM</sup></a> version. [Recommended]",
    )
