"""MITRE Technique object."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Technique(OCSFBaseModel):
    """The MITRE Technique object describes the ATT&CK® or ATLAS™ Technique ID and/or name associated to an attack.

    See: https://schema.ocsf.io/1.5.0/objects/technique
    """

    name: str | None = Field(
        default=None,
        description="The name of the attack technique. For example: <code>Active Scanning</code> or <code>AI Model Inference API Access</code>.",
    )
    src_url: Any | None = Field(
        default=None,
        description="The versioned permalink of the attack technique. For example: <code>https://attack.mitre.org/versions/v14/techniques/T1595/</code>.",
    )
    uid: str | None = Field(
        default=None,
        description="The unique identifier of the attack technique. For example: <code>T1595</code> or <code>AML.T0040</code>.",
    )
