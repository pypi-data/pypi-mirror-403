"""CIS Control object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class CisControl(OCSFBaseModel):
    """The CIS Control contains information as defined by the Center for Internet Security Critical Security Control <a target='_blank' href='https://www.cisecurity.org/controls'>(CIS CSC)</a>. Prioritized set of actions to protect your organization and data from cyber-attack vectors.

    See: https://schema.ocsf.io/1.0.0/objects/cis_control
    """

    control: str = Field(..., description="The CIS critical security control.")
    version: str | None = Field(
        default=None, description="The CIS critical security control version. [Recommended]"
    )
