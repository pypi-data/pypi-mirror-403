"""Sub Technique object."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ocsf._base import OCSFBaseModel


class SubTechnique(OCSFBaseModel):
    """The Sub Technique object describes the sub technique ID and/or name associated to an attack, as defined by <a target='_blank' href='https://attack.mitre.org/wiki/ATT&CK_Matrix'>ATT&CK Matrix<sup>TM</sup></a>.

    See: https://schema.ocsf.io/1.2.0/objects/sub_technique
    """

    name: str | None = Field(
        default=None,
        description="The name of the attack sub technique, as defined by <a target='_blank' href='https://attack.mitre.org/wiki/ATT&CK_Matrix'>ATT&CK Matrix<sup>TM</sup></a>. For example: <code>Scanning IP Blocks</code>.",
    )
    src_url: Any | None = Field(
        default=None,
        description="The versioned permalink of the attack sub technique, as defined by <a target='_blank' href='https://attack.mitre.org/wiki/ATT&CK_Matrix'>ATT&CK Matrix<sup>TM</sup></a>. For example: <code>https://attack.mitre.org/versions/v14/techniques/T1595/001/</code>.",
    )
    uid: str | None = Field(
        default=None,
        description="The unique identifier of the attack sub technique, as defined by <a target='_blank' href='https://attack.mitre.org/wiki/ATT&CK_Matrix'>ATT&CK Matrix<sup>TM</sup></a>. For example: <code>T1595.001</code>. [Recommended]",
    )
