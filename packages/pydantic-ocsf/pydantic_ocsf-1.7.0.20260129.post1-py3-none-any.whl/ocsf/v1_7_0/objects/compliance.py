"""Compliance object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.enums.status_id import StatusId
    from ocsf.v1_7_0.objects.assessment import Assessment
    from ocsf.v1_7_0.objects.check import Check
    from ocsf.v1_7_0.objects.kb_article import KbArticle
    from ocsf.v1_7_0.objects.key_value_object import KeyValueObject


class Compliance(OCSFBaseModel):
    """The Compliance object contains information about Industry and Regulatory Framework standards, controls and requirements or details about custom assessments utilized in a compliance evaluation. Standards define broad security frameworks, controls represent specific security requirements within those frameworks, and checks are the testable verification points used to determine if controls are properly implemented.

    See: https://schema.ocsf.io/1.7.0/objects/compliance
    """

    assessments: list[Assessment] | None = Field(
        default=None,
        description="A list of assessments associated with the compliance requirements evaluation.",
    )
    category: str | None = Field(
        default=None,
        description="The category a control framework pertains to, as reported by the source tool, such as <code>Asset Management</code> or <code>Risk Assessment</code>.",
    )
    checks: list[Check] | None = Field(
        default=None,
        description="A list of compliance checks associated with specific industry standards or frameworks. Each check represents an individual rule or requirement that has been evaluated against a target device. Checks typically include details such as the check name (e.g., CIS: 'Ensure mounting of cramfs filesystems is disabled' or DISA STIG descriptive titles), unique identifiers (such as CIS identifier '1.1.1.1' or DISA STIG identifier 'V-230234'), descriptions (detailed explanations of security requirements or vulnerability discussions), and version information.",
    )
    compliance_references: list[KbArticle] | None = Field(
        default=None,
        description="A list of reference KB articles that provide information to help organizations understand, interpret, and implement compliance standards. They provide guidance, best practices, and examples.",
    )
    compliance_standards: list[KbArticle] | None = Field(
        default=None,
        description="A list of established guidelines or criteria that define specific requirements an organization must follow.",
    )
    control: str | None = Field(
        default=None,
        description="A Control is a prescriptive, actionable set of specifications that strengthens device posture. The control specifies required security measures, while the specific implementation values are defined in control_parameters. E.g., CIS AWS Foundations Benchmark 1.2.0 - Control 2.1 - Ensure CloudTrail is enabled in all regions [Recommended]",
    )
    control_parameters: list[KeyValueObject] | None = Field(
        default=None,
        description="The list of control parameters evaluated in a Compliance check. E.g., parameters for CloudTrail configuration might include <code>multiRegionTrailEnabled: true</code>, <code>logFileValidationEnabled: true</code>, and <code>requiredRegions: [us-east-1, us-west-2]</code>",
    )
    desc: str | None = Field(default=None, description="The description or criteria of a control.")
    requirements: list[str] | None = Field(
        default=None,
        description="The specific compliance requirements being evaluated. E.g., <code>PCI DSS Requirement 8.2.3 - Passwords must meet minimum complexity requirements</code> or <code>HIPAA Security Rule 164.312(a)(2)(iv) - Implement encryption and decryption mechanisms</code>",
    )
    standards: list[str] | None = Field(
        default=None,
        description="The regulatory or industry standards being evaluated for compliance. [Recommended]",
    )
    status: str | None = Field(
        default=None,
        description="The resultant status of the compliance check normalized to the caption of the <code>status_id</code> value. In the case of 'Other', it is defined by the event source. [Recommended]",
    )
    status_code: str | None = Field(
        default=None, description="The resultant status code of the compliance check."
    )
    status_detail: str | None = Field(
        default=None,
        description="The contextual description of the <code>status, status_code</code> values.",
    )
    status_details: list[str] | None = Field(
        default=None,
        description="A list of contextual descriptions of the <code>status, status_code</code> values.",
    )
    status_id: StatusId | None = Field(
        default=None,
        description="The normalized status identifier of the compliance check. [Recommended]",
    )
