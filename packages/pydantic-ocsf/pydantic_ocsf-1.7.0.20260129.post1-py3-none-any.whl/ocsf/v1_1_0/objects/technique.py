"""Technique object."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Technique(OCSFBaseModel):
    """The Technique object describes the technique ID and/or name associated to an attack, as defined by <a target='_blank' href='https://attack.mitre.org/wiki/ATT&CK_Matrix'>ATT&CK Matrix<sup>TM</sup></a>.

    See: https://schema.ocsf.io/1.1.0/objects/technique
    """

    name: str | None = Field(
        default=None,
        description="The name of the attack technique, as defined by <a target='_blank' href='https://attack.mitre.org/wiki/ATT&CK_Matrix'>ATT&CK Matrix<sup>TM</sup></a>. For example: <code>Active Scanning</code>.",
    )
    src_url: Any | None = Field(
        default=None,
        description="The versioned permalink of the attack technique, as defined by <a target='_blank' href='https://attack.mitre.org/wiki/ATT&CK_Matrix'>ATT&CK Matrix<sup>TM</sup></a>. For example: <code>https://attack.mitre.org/versions/v14/techniques/T1595/</code>.",
    )
    uid: str | None = Field(
        default=None,
        description="The unique identifier of the attack technique, as defined by <a target='_blank' href='https://attack.mitre.org/wiki/ATT&CK_Matrix'>ATT&CK Matrix<sup>TM</sup></a>. For example: <code>T1595</code>.",
    )
