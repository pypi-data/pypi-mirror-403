"""EPSS object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Epss(OCSFBaseModel):
    """The Exploit Prediction Scoring System (EPSS) object describes the estimated probability a vulnerability will be exploited. EPSS is a community-driven effort to combine descriptive information about vulnerabilities (CVEs) with evidence of actual exploitation in-the-wild. (<a target='_blank' href='https://www.first.org/epss/'>EPSS</a>).

    See: https://schema.ocsf.io/1.5.0/objects/epss
    """

    score: str = Field(
        ...,
        description="The EPSS score representing the probability [0-1] of exploitation in the wild in the next 30 days (following score publication).",
    )
    created_time: int | None = Field(
        default=None,
        description="The timestamp indicating when the EPSS score was calculated. [Recommended]",
    )
    percentile: float | None = Field(
        default=None,
        description="The EPSS score's percentile representing relative importance and ranking of the score in the larger EPSS dataset.",
    )
    version: str | None = Field(
        default=None,
        description="The version of the EPSS model used to calculate the score. [Recommended]",
    )
