"""IAM Analysis Finding event class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.enums.activity_id import ActivityId
    from ocsf.v1_6_0.enums.confidence_id import ConfidenceId
    from ocsf.v1_6_0.enums.severity_id import SeverityId
    from ocsf.v1_6_0.enums.status_id import StatusId
    from ocsf.v1_6_0.objects.access_analysis_result import AccessAnalysisResult
    from ocsf.v1_6_0.objects.application import Application
    from ocsf.v1_6_0.objects.device import Device
    from ocsf.v1_6_0.objects.enrichment import Enrichment
    from ocsf.v1_6_0.objects.finding_info import FindingInfo
    from ocsf.v1_6_0.objects.fingerprint import Fingerprint
    from ocsf.v1_6_0.objects.identity_activity_metrics import IdentityActivityMetrics
    from ocsf.v1_6_0.objects.metadata import Metadata
    from ocsf.v1_6_0.objects.object import Object
    from ocsf.v1_6_0.objects.observable import Observable
    from ocsf.v1_6_0.objects.permission_analysis_result import PermissionAnalysisResult
    from ocsf.v1_6_0.objects.remediation import Remediation
    from ocsf.v1_6_0.objects.resource_details import ResourceDetails
    from ocsf.v1_6_0.objects.user import User
    from ocsf.v1_6_0.objects.vendor_attributes import VendorAttributes


class IamAnalysisFinding(OCSFBaseModel):
    """This finding represents an IAM analysis result, which evaluates IAM policies, access patterns, and IAM configurations for potential security risks. The analysis can focus on either an identity (user, role, service account) or a resource to assess permissions, access patterns, and security posture within the IAM domain. <br><strong>Note:</strong> Use <code>permission_analysis_results</code> for identity-centric analysis (evaluating what an identity can do) and <code>access_analysis_result</code> for resource-centric analysis (evaluating who can access a resource). These complement each other for comprehensive IAM security assessment.<br><strong>Note:</strong> If the Finding is an incident, i.e. requires incident workflow, also apply the <code>incident</code> profile or aggregate this finding into an <code>Incident Finding</code>.

    OCSF Class UID: 8
    Category:

    See: https://schema.ocsf.io/1.6.0/classes/iam_analysis_finding
    """

    # Class identifiers
    class_uid: Literal[8] = Field(
        default=8, description="The unique identifier of the event class."
    )
    category_uid: Literal[0] = Field(default=0, description="The category unique identifier.")
    finding_info: FindingInfo = Field(
        ..., description="Describes the supporting information about a generated finding."
    )
    metadata: Metadata = Field(
        ..., description="The metadata associated with the event or a finding."
    )
    severity_id: SeverityId = Field(
        ...,
        description="<p>The normalized identifier of the event/finding severity.</p>The normalized severity is a measurement the effort and expense required to manage and resolve an event or incident. Smaller numerical values represent lower impact events, and larger numerical values represent higher impact events.",
    )
    time: int = Field(
        ..., description="The normalized event occurrence time or the finding creation time."
    )
    type_uid: int = Field(
        ...,
        description="The event/finding type ID. It identifies the event's semantics and structure. The value is calculated by the logging system as: <code>class_uid * 100 + activity_id</code>.",
    )
    access_analysis_result: AccessAnalysisResult | None = Field(
        default=None,
        description="Describes access relationships and pathways between identities, resources, focusing on who can access what and through which mechanisms. This evaluates access levels (read/write/admin), access types (direct, cross-account, public, federated), and the conditions under which access is granted. Use this for resource-centric security assessments such as external access discovery, public exposure analysis, etc.",
    )
    activity_id: ActivityId | None = Field(
        default=None, description="The normalized identifier of the finding activity."
    )
    activity_name: str | None = Field(
        default=None,
        description="The finding activity name, as defined by the <code>activity_id</code>.",
    )
    applications: list[Application] | None = Field(
        default=None,
        description="Details about applications, services, or systems that are accessible based on the IAM analysis. For identity-centric analysis, this represents applications the identity can access. For resource-centric analysis, this represents applications that can access the resource. [Recommended]",
    )
    category_name: str | None = Field(
        default=None, description="The event category name, as defined by category_uid value."
    )
    class_name: str | None = Field(
        default=None, description="The event class name, as defined by class_uid value."
    )
    comment: str | None = Field(
        default=None, description="A user provided comment about the finding."
    )
    confidence: str | None = Field(
        default=None,
        description="The confidence, normalized to the caption of the confidence_id value. In the case of 'Other', it is defined by the event source.",
    )
    confidence_id: ConfidenceId | None = Field(
        default=None,
        description="The normalized confidence refers to the accuracy of the rule that created the finding. A rule with a low confidence means that the finding scope is wide and may create finding reports that may not be malicious in nature. [Recommended]",
    )
    confidence_score: int | None = Field(
        default=None, description="The confidence score as reported by the event source."
    )
    count: int | None = Field(
        default=None,
        description="The number of times that events in the same logical group occurred during the event <strong>Start Time</strong> to <strong>End Time</strong> period.",
    )
    device: Device | None = Field(
        default=None,
        description="Describes the affected device/host. If applicable, it can be used in conjunction with <code>Resource(s)</code>. <p> e.g. Specific details about an AWS EC2 instance, that is affected by the Finding.</p>",
    )
    duration: int | None = Field(
        default=None,
        description="The event duration or aggregate time, the amount of time the event covers from <code>start_time</code> to <code>end_time</code> in milliseconds.",
    )
    end_time: int | None = Field(
        default=None, description="The time of the most recent event included in the finding."
    )
    enrichments: list[Enrichment] | None = Field(
        default=None,
        description='The additional information from an external data source, which is associated with the event or a finding. For example add location information for the IP address in the DNS answers:</p><code>[{"name": "answers.ip", "value": "92.24.47.250", "type": "location", "data": {"city": "Socotra", "continent": "Asia", "coordinates": [-25.4153, 17.0743], "country": "YE", "desc": "Yemen"}}]</code>',
    )
    identity_activity_metrics: IdentityActivityMetrics | None = Field(
        default=None,
        description="Describes usage activity and other metrics of an Identity i.e. AWS IAM User, GCP IAM Principal, etc. [Recommended]",
    )
    include: str | None = Field(default=None, description="")
    message: str | None = Field(
        default=None,
        description="The description of the event/finding, as defined by the source. [Recommended]",
    )
    observables: list[Observable] | None = Field(
        default=None,
        description="The observables associated with the event or a finding. [Recommended]",
    )
    permission_analysis_results: list[PermissionAnalysisResult] | None = Field(
        default=None,
        description="Describes analysis results of permissions, policies directly associated with an identity (user, role, or service account). This evaluates what permissions an identity has been granted through attached policies, which privileges are actively used versus unused, and identifies potential over-privileged access. Use this for identity-centric security assessments such as privilege audits, dormant permission discovery, and least-privilege compliance analysis. [Recommended]",
    )
    raw_data: str | None = Field(
        default=None, description="The raw event/finding data as received from the source."
    )
    raw_data_hash: Fingerprint | None = Field(
        default=None, description="The hash, which describes the content of the raw_data field."
    )
    raw_data_size: int | None = Field(
        default=None,
        description="The size of the raw data which was transformed into an OCSF event, in bytes.",
    )
    remediation: Remediation | None = Field(
        default=None,
        description="Describes the recommended remediation steps to address identified issue(s).",
    )
    resources: list[ResourceDetails] | None = Field(
        default=None,
        description="Details about resources involved in the IAM analysis. For identity-centric analysis, this represents resources the identity can access. For resource-centric analysis, this represents the resource being analyzed and related resources in the access chain. [Recommended]",
    )
    severity: str | None = Field(
        default=None,
        description="The event/finding severity, normalized to the caption of the <code>severity_id</code> value. In the case of 'Other', it is defined by the source.",
    )
    start_time: int | None = Field(
        default=None, description="The time of the least recent event included in the finding."
    )
    status: str | None = Field(
        default=None,
        description="The normalized status of the Finding set by the consumer normalized to the caption of the status_id value. In the case of 'Other', it is defined by the source.",
    )
    status_code: str | None = Field(
        default=None,
        description="The event status code, as reported by the event source.<br /><br />For example, in a Windows Failed Authentication event, this would be the value of 'Failure Code', e.g. 0x18. [Recommended]",
    )
    status_detail: str | None = Field(
        default=None,
        description="The status detail contains additional information about the event/finding outcome. [Recommended]",
    )
    status_id: StatusId | None = Field(
        default=None,
        description="The normalized status identifier of the Finding, set by the consumer. [Recommended]",
    )
    timezone_offset: int | None = Field(
        default=None,
        description="The number of minutes that the reported event <code>time</code> is ahead or behind UTC, in the range -1,080 to +1,080. [Recommended]",
    )
    type_name: str | None = Field(
        default=None, description="The event/finding type name, as defined by the type_uid."
    )
    unmapped: Object | None = Field(
        default=None,
        description="The attributes that are not mapped to the event schema. The names and values of those attributes are specific to the event source.",
    )
    user: User | None = Field(
        default=None,
        description="Details about the identity (user, role, service account, or other principal) that is the subject of the IAM analysis. This provides context about the identity being evaluated for security risks and access patterns. [Recommended]",
    )
    vendor_attributes: VendorAttributes | None = Field(
        default=None,
        description="The Vendor Attributes object can be used to represent values of attributes populated by the Vendor/Finding Provider. It can help distinguish between the vendor-provided values and consumer-updated values, of key attributes like <code>severity_id</code>.<br>The original finding producer should not populate this object. It should be populated by consuming systems that support data mutability.",
    )
