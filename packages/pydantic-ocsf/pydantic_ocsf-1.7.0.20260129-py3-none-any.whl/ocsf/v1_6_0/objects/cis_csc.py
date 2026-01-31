"""CIS CSC object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class CisCsc(OCSFBaseModel):
    """The CIS Critical Security Control (CSC) contains information as defined by the Center for Internet Security Critical Security Control <a target='_blank' href='https://www.cisecurity.org/controls'>(CIS CSC)</a>. Prioritized set of actions to protect your organization and data from cyber-attack vectors.

    See: https://schema.ocsf.io/1.6.0/objects/cis_csc
    """

    control: str = Field(
        ...,
        description="A Control is prescriptive, prioritized, and simplified set of best practices that one can use to strengthen their cybersecurity posture. e.g. AWS SecurityHub Controls, CIS Controls.",
    )
    version: str | None = Field(
        default=None, description="The CIS critical security control version. [Recommended]"
    )
