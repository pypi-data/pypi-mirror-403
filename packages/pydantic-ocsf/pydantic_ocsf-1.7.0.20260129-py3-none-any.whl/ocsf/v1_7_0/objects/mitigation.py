"""MITRE Mitigation object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.objects.d3fend import D3fend


class Mitigation(OCSFBaseModel):
    """The MITRE Mitigation object describes the ATT&CK® or ATLAS™ Mitigation ID and/or name that is associated to an attack.

    See: https://schema.ocsf.io/1.7.0/objects/mitigation
    """

    countermeasures: list[D3fend] | None = Field(
        default=None,
        description="The D3FEND countermeasures that are associated with the attack technique. For example: ATT&CK Technique <code>T1003</code> is addressed by Mitigation <code>M1027</code>, and D3FEND Technique <code>D3-OTP</code>.",
    )
    name: str | None = Field(
        default=None,
        description="The Mitigation name that is associated with the attack technique. For example: <code>Password Policies</code>, or <code>Code Signing</code>.",
    )
    src_url: Any | None = Field(
        default=None,
        description="The versioned permalink of the Mitigation. For example: <code>https://attack.mitre.org/versions/v14/mitigations/M1027</code>.",
    )
    uid: str | None = Field(
        default=None,
        description="The Mitigation ID that is associated with the attack technique. For example: <code>M1027</code>, or <code>AML.M0013</code>.",
    )
