"""Technique object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Technique(OCSFBaseModel):
    """The Technique object describes the technique related to an attack, as defined by <a target='_blank' href='https://attack.mitre.org/wiki/ATT&CK_Matrix'>ATT&CK Matrix<sup>TM</sup></a>.

    See: https://schema.ocsf.io/1.0.0/objects/technique
    """

    name: str | None = Field(
        default=None,
        description="The name of the attack technique, as defined by <a target='_blank' href='https://attack.mitre.org/wiki/ATT&CK_Matrix'>ATT&CK Matrix<sup>TM</sup></a>. For example: <code>Drive-by Compromise</code>.",
    )
    uid: str | None = Field(
        default=None,
        description="The unique identifier of the attack technique, as defined by <a target='_blank' href='https://attack.mitre.org/wiki/ATT&CK_Matrix'>ATT&CK Matrix<sup>TM</sup></a>. For example: <code>T1189</code>.",
    )
