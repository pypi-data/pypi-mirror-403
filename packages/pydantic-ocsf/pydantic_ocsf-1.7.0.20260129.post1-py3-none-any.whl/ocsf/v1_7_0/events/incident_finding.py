"""Incident Finding event class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.enums.activity_id import ActivityId
    from ocsf.v1_7_0.enums.confidence_id import ConfidenceId
    from ocsf.v1_7_0.enums.impact_id import ImpactId
    from ocsf.v1_7_0.enums.priority_id import PriorityId
    from ocsf.v1_7_0.enums.severity_id import SeverityId
    from ocsf.v1_7_0.enums.status_id import StatusId
    from ocsf.v1_7_0.enums.verdict_id import VerdictId
    from ocsf.v1_7_0.objects.attack import Attack
    from ocsf.v1_7_0.objects.enrichment import Enrichment
    from ocsf.v1_7_0.objects.finding_info import FindingInfo
    from ocsf.v1_7_0.objects.fingerprint import Fingerprint
    from ocsf.v1_7_0.objects.group import Group
    from ocsf.v1_7_0.objects.metadata import Metadata
    from ocsf.v1_7_0.objects.object import Object
    from ocsf.v1_7_0.objects.observable import Observable
    from ocsf.v1_7_0.objects.ticket import Ticket
    from ocsf.v1_7_0.objects.user import User
    from ocsf.v1_7_0.objects.vendor_attributes import VendorAttributes


class IncidentFinding(OCSFBaseModel):
    """An Incident Finding reports the creation, update, or closure of security incidents as a result of detections and/or analytics. <br><strong>Note: </strong><code>Incident Finding</code> implicitly includes the <code>incident</code> profile and it should be added to the <code>metadata.profiles[]</code> array.

    OCSF Class UID: 5
    Category: findings

    See: https://schema.ocsf.io/1.7.0/classes/incident_finding
    """

    # Class identifiers
    class_uid: Literal[5] = Field(
        default=5, description="The unique identifier of the event class."
    )
    category_uid: Literal[0] = Field(default=0, description="The category unique identifier.")
    activity_id: ActivityId = Field(
        ..., description="The normalized identifier of the Incident activity."
    )
    finding_info_list: list[FindingInfo] = Field(
        ..., description="A list of <code>finding_info</code> objects associated to an incident."
    )
    metadata: Metadata = Field(
        ..., description="The metadata associated with the event or a finding."
    )
    severity_id: SeverityId = Field(
        ...,
        description="<p>The normalized identifier of the event/finding severity.</p>The normalized severity is a measurement the effort and expense required to manage and resolve an event or incident. Smaller numerical values represent lower impact events, and larger numerical values represent higher impact events.",
    )
    status_id: StatusId = Field(
        ..., description="The normalized status identifier of the Incident."
    )
    time: int = Field(
        ..., description="The normalized event occurrence time or the finding creation time."
    )
    type_uid: int = Field(
        ...,
        description="The event/finding type ID. It identifies the event's semantics and structure. The value is calculated by the logging system as: <code>class_uid * 100 + activity_id</code>.",
    )
    activity_name: str | None = Field(
        default=None,
        description="The Incident activity name, as defined by the <code>activity_id</code>.",
    )
    assignee: User | None = Field(
        default=None, description="The details of the user assigned to an Incident."
    )
    assignee_group: Group | None = Field(
        default=None, description="The details of the group assigned to an Incident."
    )
    attacks: list[Attack] | None = Field(
        default=None,
        description="An array of <a target='_blank' href='https://attack.mitre.org'>MITRE ATT&CK®</a> objects describing the tactics, techniques & sub-techniques associated to the Incident.",
    )
    category_name: str | None = Field(
        default=None, description="The event category name, as defined by category_uid value."
    )
    class_name: str | None = Field(
        default=None, description="The event class name, as defined by class_uid value."
    )
    comment: str | None = Field(
        default=None,
        description="Additional user supplied details for updating or closing the incident.",
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
    desc: str | None = Field(
        default=None, description="The short description of the Incident. [Recommended]"
    )
    duration: int | None = Field(
        default=None,
        description="The event duration or aggregate time, the amount of time the event covers from <code>start_time</code> to <code>end_time</code> in milliseconds.",
    )
    end_time: int | None = Field(
        default=None, description="The time of the most recent event included in the incident."
    )
    enrichments: list[Enrichment] | None = Field(
        default=None,
        description='The additional information from an external data source, which is associated with the event or a finding. For example add location information for the IP address in the DNS answers:</p><code>[{"name": "answers.ip", "value": "92.24.47.250", "type": "location", "data": {"city": "Socotra", "continent": "Asia", "coordinates": [-25.4153, 17.0743], "country": "YE", "desc": "Yemen"}}]</code>',
    )
    impact: str | None = Field(
        default=None,
        description="The impact , normalized to the caption of the impact_id value. In the case of 'Other', it is defined by the event source. [Recommended]",
    )
    impact_id: ImpactId | None = Field(
        default=None,
        description="The normalized impact of the incident or finding. Per NIST, this is the magnitude of harm that can be expected to result from the consequences of unauthorized disclosure, modification, destruction, or loss of information or information system availability. [Recommended]",
    )
    impact_score: int | None = Field(
        default=None,
        description="The impact as an integer value of the finding, valid range 0-100. [Recommended]",
    )
    include: str | None = Field(default=None, description="")
    is_suspected_breach: bool | None = Field(
        default=None,
        description="A determination based on analytics as to whether a potential breach was found.",
    )
    message: str | None = Field(
        default=None,
        description="The description of the event/finding, as defined by the source. [Recommended]",
    )
    observables: list[Observable] | None = Field(
        default=None,
        description="The observables associated with the event or a finding. [Recommended]",
    )
    priority: str | None = Field(
        default=None,
        description="The priority, normalized to the caption of the priority_id value. In the case of 'Other', it is defined by the event source.",
    )
    priority_id: PriorityId | None = Field(
        default=None,
        description="The normalized priority. Priority identifies the relative importance of the incident or finding. It is a measurement of urgency. [Recommended]",
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
    severity: str | None = Field(
        default=None,
        description="The event/finding severity, normalized to the caption of the <code>severity_id</code> value. In the case of 'Other', it is defined by the source.",
    )
    src_url: Any | None = Field(
        default=None, description="A Url link used to access the original incident. [Recommended]"
    )
    start_time: int | None = Field(
        default=None, description="The time of the least recent event included in the incident."
    )
    status: str | None = Field(
        default=None,
        description="The normalized status of the Incident normalized to the caption of the status_id value. In the case of 'Other', it is defined by the source. [Recommended]",
    )
    status_code: str | None = Field(
        default=None,
        description="The event status code, as reported by the event source.<br /><br />For example, in a Windows Failed Authentication event, this would be the value of 'Failure Code', e.g. 0x18. [Recommended]",
    )
    status_detail: str | None = Field(
        default=None,
        description="The status detail contains additional information about the event/finding outcome. [Recommended]",
    )
    ticket: Ticket | None = Field(
        default=None, description="The linked ticket in the ticketing system."
    )
    tickets: list[Ticket] | None = Field(
        default=None,
        description="The associated ticket(s) in the ticketing system. Each ticket contains details like ticket ID, status, etc.",
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
    vendor_attributes: VendorAttributes | None = Field(
        default=None,
        description="The Vendor Attributes object can be used to represent values of attributes populated by the Vendor/Finding Provider. It can help distinguish between the vendor-provided values and consumer-updated values, of key attributes like <code>severity_id</code>.<br>The original finding producer should not populate this object. It should be populated by consuming systems that support data mutability.",
    )
    verdict: str | None = Field(
        default=None, description="The verdict assigned to an Incident finding. [Recommended]"
    )
    verdict_id: VerdictId | None = Field(
        default=None, description="The normalized verdict of an Incident. [Recommended]"
    )
