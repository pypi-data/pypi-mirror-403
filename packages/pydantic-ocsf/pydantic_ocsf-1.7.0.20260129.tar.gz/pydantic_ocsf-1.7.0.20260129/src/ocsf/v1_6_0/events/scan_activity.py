"""Scan Activity event class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.enums.activity_id import ActivityId
    from ocsf.v1_6_0.enums.severity_id import SeverityId
    from ocsf.v1_6_0.enums.status_id import StatusId
    from ocsf.v1_6_0.objects.enrichment import Enrichment
    from ocsf.v1_6_0.objects.fingerprint import Fingerprint
    from ocsf.v1_6_0.objects.metadata import Metadata
    from ocsf.v1_6_0.objects.object import Object
    from ocsf.v1_6_0.objects.observable import Observable
    from ocsf.v1_6_0.objects.policy import Policy
    from ocsf.v1_6_0.objects.scan import Scan


class ScanActivity(OCSFBaseModel):
    """Scan events report the start, completion, and results of a scan job. The scan event includes the number of items that were scanned and the number of detections that were resolved.

    OCSF Class UID: 7
    Category:

    See: https://schema.ocsf.io/1.6.0/classes/scan_activity
    """

    # Class identifiers
    class_uid: Literal[7] = Field(
        default=7, description="The unique identifier of the event class."
    )
    category_uid: Literal[0] = Field(default=0, description="The category unique identifier.")
    metadata: Metadata = Field(
        ..., description="The metadata associated with the event or a finding."
    )
    scan: Scan = Field(
        ..., description="The Scan object describes characteristics of the scan job."
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
    activity_id: ActivityId | None = Field(
        default=None,
        description="The normalized identifier of the activity that triggered the event.",
    )
    activity_name: str | None = Field(
        default=None, description="The event activity name, as defined by the activity_id."
    )
    category_name: str | None = Field(
        default=None, description="The event category name, as defined by category_uid value."
    )
    class_name: str | None = Field(
        default=None, description="The event class name, as defined by class_uid value."
    )
    command_uid: str | None = Field(
        default=None,
        description="The command identifier that is associated with this scan event.  This ID uniquely identifies the proactive scan command, e.g., if remotely initiated. [Recommended]",
    )
    count: int | None = Field(
        default=None,
        description="The number of times that events in the same logical group occurred during the event <strong>Start Time</strong> to <strong>End Time</strong> period.",
    )
    duration: int | None = Field(default=None, description="The duration of the scan [Recommended]")
    end_time: int | None = Field(
        default=None, description="The end time of the scan job. [Recommended]"
    )
    enrichments: list[Enrichment] | None = Field(
        default=None,
        description='The additional information from an external data source, which is associated with the event or a finding. For example add location information for the IP address in the DNS answers:</p><code>[{"name": "answers.ip", "value": "92.24.47.250", "type": "location", "data": {"city": "Socotra", "continent": "Asia", "coordinates": [-25.4153, 17.0743], "country": "YE", "desc": "Yemen"}}]</code>',
    )
    include: str | None = Field(default=None, description="")
    message: str | None = Field(
        default=None,
        description="The description of the event/finding, as defined by the source. [Recommended]",
    )
    num_detections: int | None = Field(
        default=None, description="The number of detections. [Recommended]"
    )
    num_files: int | None = Field(
        default=None, description="The number of files scanned. [Recommended]"
    )
    num_folders: int | None = Field(
        default=None, description="The number of folders scanned. [Recommended]"
    )
    num_network_items: int | None = Field(
        default=None, description="The number of network items scanned. [Recommended]"
    )
    num_processes: int | None = Field(
        default=None, description="The number of processes scanned. [Recommended]"
    )
    num_registry_items: int | None = Field(
        default=None, description="The number of registry items scanned. [Recommended]"
    )
    num_resolutions: int | None = Field(
        default=None, description="The number of items that were resolved. [Recommended]"
    )
    num_skipped_items: int | None = Field(
        default=None, description="The number of skipped items. [Recommended]"
    )
    num_trusted_items: int | None = Field(
        default=None, description="The number of trusted items. [Recommended]"
    )
    observables: list[Observable] | None = Field(
        default=None,
        description="The observables associated with the event or a finding. [Recommended]",
    )
    policy: Policy | None = Field(
        default=None,
        description="The policy associated with this Scan event; required if the scan was initiated by a policy. [Recommended]",
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
    schedule_uid: str | None = Field(
        default=None,
        description="The unique identifier of the schedule associated with a scan job. [Recommended]",
    )
    severity: str | None = Field(
        default=None,
        description="The event/finding severity, normalized to the caption of the <code>severity_id</code> value. In the case of 'Other', it is defined by the source.",
    )
    start_time: int | None = Field(
        default=None, description="The start time of the scan job. [Recommended]"
    )
    status: str | None = Field(
        default=None,
        description="The event status, normalized to the caption of the status_id value. In the case of 'Other', it is defined by the event source. [Recommended]",
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
        default=None, description="The normalized identifier of the event status. [Recommended]"
    )
    timezone_offset: int | None = Field(
        default=None,
        description="The number of minutes that the reported event <code>time</code> is ahead or behind UTC, in the range -1,080 to +1,080. [Recommended]",
    )
    total: int | None = Field(
        default=None,
        description="The total number of items that were scanned; zero if no items were scanned. [Recommended]",
    )
    type_name: str | None = Field(
        default=None, description="The event/finding type name, as defined by the type_uid."
    )
    unmapped: Object | None = Field(
        default=None,
        description="The attributes that are not mapped to the event schema. The names and values of those attributes are specific to the event source.",
    )
