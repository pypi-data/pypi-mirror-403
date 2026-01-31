"""Compliance object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_2_0.enums.status_id import StatusId


class Compliance(OCSFBaseModel):
    """The Compliance object contains information about Industry and Regulatory Framework standards, controls and requirements.

    See: https://schema.ocsf.io/1.2.0/objects/compliance
    """

    standards: list[str] = Field(
        ...,
        description="Security standards are a set of criteria organizations can follow to protect sensitive and confidential information. e.g. <code>NIST SP 800-53, CIS AWS Foundations Benchmark v1.4.0, ISO/IEC 27001</code>",
    )
    control: str | None = Field(
        default=None,
        description="A Control is prescriptive, prioritized, and simplified set of best practices that one can use to strengthen their cybersecurity posture. e.g. AWS SecurityHub Controls, CIS Controls. [Recommended]",
    )
    requirements: list[str] | None = Field(
        default=None,
        description="A list of requirements associated to a specific control in an industry or regulatory framework. e.g. <code> NIST.800-53.r5 AU-10 </code>",
    )
    status: str | None = Field(
        default=None,
        description="The resultant status of the compliance check  normalized to the caption of the <code>status_id</code> value. In the case of 'Other', it is defined by the event source. [Recommended]",
    )
    status_code: str | None = Field(
        default=None, description="The resultant status code of the compliance check."
    )
    status_detail: str | None = Field(
        default=None, description="The contextual description of the status, status_code values."
    )
    status_id: StatusId | None = Field(
        default=None,
        description="The normalized status identifier of the compliance check. [Recommended]",
    )
