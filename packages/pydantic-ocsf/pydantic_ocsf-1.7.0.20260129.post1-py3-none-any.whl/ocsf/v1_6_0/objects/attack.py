"""MITRE ATT&CK® & ATLAS™ object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.objects.mitigation import Mitigation
    from ocsf.v1_6_0.objects.sub_technique import SubTechnique
    from ocsf.v1_6_0.objects.tactic import Tactic
    from ocsf.v1_6_0.objects.technique import Technique


class Attack(OCSFBaseModel):
    """The MITRE ATT&CK® & ATLAS™ object describes the tactic, technique, sub-technique & mitigation associated to an attack.

    See: https://schema.ocsf.io/1.6.0/objects/attack
    """

    mitigation: Mitigation | None = Field(
        default=None,
        description="The Mitigation object describes the MITRE ATT&CK® or ATLAS™ Mitigation ID and/or name that is associated to an attack.",
    )
    sub_technique: SubTechnique | None = Field(
        default=None,
        description="The Sub-technique object describes the MITRE ATT&CK® or ATLAS™ Sub-technique ID and/or name associated to an attack. [Recommended]",
    )
    tactic: Tactic | None = Field(
        default=None,
        description="The Tactic object describes the MITRE ATT&CK® or ATLAS™ Tactic ID and/or name that is associated to an attack. [Recommended]",
    )
    tactics: list[Tactic] | None = Field(
        default=None,
        description="The Tactic object describes the tactic ID and/or tactic name that are associated with the attack technique, as defined by <a target='_blank' href='https://attack.mitre.org/wiki/ATT&CK_Matrix'>ATT&CK® Matrix</a>.",
    )
    technique: Technique | None = Field(
        default=None,
        description="The Technique object describes the MITRE ATT&CK® or ATLAS™ Technique ID and/or name associated to an attack. [Recommended]",
    )
    version: str | None = Field(
        default=None, description="The ATT&CK® or ATLAS™ Matrix version. [Recommended]"
    )
