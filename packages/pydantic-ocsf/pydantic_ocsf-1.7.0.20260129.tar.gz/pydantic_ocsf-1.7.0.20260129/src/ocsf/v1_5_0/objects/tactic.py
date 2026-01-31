"""MITRE Tactic object."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Tactic(OCSFBaseModel):
    """The MITRE Tactic object describes the ATT&CK® or ATLAS™ Tactic ID and/or name that is associated to an attack.

    See: https://schema.ocsf.io/1.5.0/objects/tactic
    """

    name: str | None = Field(
        default=None,
        description="The Tactic name that is associated with the attack technique. For example: <code>Reconnaissance</code> or <code>ML Model Access</code>.",
    )
    src_url: Any | None = Field(
        default=None,
        description="The versioned permalink of the Tactic. For example: <code>https://attack.mitre.org/versions/v14/tactics/TA0043/</code>.",
    )
    uid: str | None = Field(
        default=None,
        description="The Tactic ID that is associated with the attack technique. For example: <code>TA0043</code>, or <code>AML.TA0000</code>.",
    )
