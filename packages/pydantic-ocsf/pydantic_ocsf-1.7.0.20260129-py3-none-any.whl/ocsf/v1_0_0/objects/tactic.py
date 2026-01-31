"""Tactic object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Tactic(OCSFBaseModel):
    """The Tactic object describes the tactic IDs and/or name that are associated with the attack technique, as defined by <a target='_blank' href='https://attack.mitre.org/wiki/ATT&CK_Matrix'>ATT&CK Matrix<sup>TM</sup></a>.

    See: https://schema.ocsf.io/1.0.0/objects/tactic
    """

    name: str | None = Field(
        default=None,
        description="The tactic name that is associated with the attack technique, as defined by <a target='_blank' href='https://attack.mitre.org/wiki/ATT&CK_Matrix'>ATT&CK Matrix<sup>TM</sup></a>.",
    )
    uid: str | None = Field(
        default=None,
        description="The tactic ID that is associated with the attack technique, as defined by <a target='_blank' href='https://attack.mitre.org/wiki/ATT&CK_Matrix'>ATT&CK Matrix<sup>TM</sup></a>.",
    )
