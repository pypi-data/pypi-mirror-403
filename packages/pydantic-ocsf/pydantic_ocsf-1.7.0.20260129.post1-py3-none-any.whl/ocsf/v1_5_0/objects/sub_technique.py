"""MITRE Sub-technique object."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ocsf._base import OCSFBaseModel


class SubTechnique(OCSFBaseModel):
    """The MITRE Sub-technique object describes the ATT&CK® or ATLAS™ Sub-technique ID and/or name associated to an attack.

    See: https://schema.ocsf.io/1.5.0/objects/sub_technique
    """

    name: str | None = Field(
        default=None,
        description="The name of the attack sub-technique. For example: <code>Scanning IP Blocks</code> or <code>User Execution: Unsafe ML Artifacts</code>.",
    )
    src_url: Any | None = Field(
        default=None,
        description="The versioned permalink of the attack sub-technique. For example: <code>https://attack.mitre.org/versions/v14/techniques/T1595/001/</code>.",
    )
    uid: str | None = Field(
        default=None,
        description="The unique identifier of the attack sub-technique. For example: <code>T1595.001</code> or <code>AML.T0011.000</code>.",
    )
