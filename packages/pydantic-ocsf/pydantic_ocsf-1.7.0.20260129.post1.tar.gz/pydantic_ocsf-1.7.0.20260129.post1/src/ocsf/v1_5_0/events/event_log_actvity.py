"""Event Log Activity event class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.activity_id import ActivityId
    from ocsf.v1_5_0.enums.log_type_id import LogTypeId
    from ocsf.v1_5_0.enums.severity_id import SeverityId
    from ocsf.v1_5_0.enums.status_id import StatusId
    from ocsf.v1_5_0.objects.actor import Actor
    from ocsf.v1_5_0.objects.device import Device
    from ocsf.v1_5_0.objects.enrichment import Enrichment
    from ocsf.v1_5_0.objects.file import File
    from ocsf.v1_5_0.objects.metadata import Metadata
    from ocsf.v1_5_0.objects.network_endpoint import NetworkEndpoint
    from ocsf.v1_5_0.objects.object import Object
    from ocsf.v1_5_0.objects.observable import Observable


class EventLogActvity(OCSFBaseModel):
    """Event Log Activity events report actions pertaining to the system's event logging service(s), such as disabling logging or clearing the log data.

    OCSF Class UID: 8
    Category:

    See: https://schema.ocsf.io/1.5.0/classes/event_log_actvity
    """

    # Class identifiers
    class_uid: Literal[8] = Field(
        default=8, description="The unique identifier of the event class."
    )
    category_uid: Literal[0] = Field(default=0, description="The category unique identifier.")
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
    activity_id: ActivityId | None = Field(
        default=None,
        description="The normalized identifier of the activity that triggered the event.",
    )
    activity_name: str | None = Field(
        default=None, description="The event activity name, as defined by the activity_id."
    )
    actor: Actor | None = Field(
        default=None, description="The actor that performed the activity. [Recommended]"
    )
    category_name: str | None = Field(
        default=None, description="The event category name, as defined by category_uid value."
    )
    class_name: str | None = Field(
        default=None, description="The event class name, as defined by class_uid value."
    )
    count: int | None = Field(
        default=None,
        description="The number of times that events in the same logical group occurred during the event <strong>Start Time</strong> to <strong>End Time</strong> period.",
    )
    device: Device | None = Field(
        default=None, description="The device that reported the event. [Recommended]"
    )
    dst_endpoint: NetworkEndpoint | None = Field(
        default=None,
        description="The <p style='display:inline;color:red'>targeted</p> endpoint for the event log activity. [Recommended]",
    )
    duration: int | None = Field(
        default=None,
        description="The event duration or aggregate time, the amount of time the event covers from <code>start_time</code> to <code>end_time</code> in milliseconds.",
    )
    end_time: int | None = Field(
        default=None,
        description="The end time of a time period, or the time of the most recent event included in the aggregate event.",
    )
    enrichments: list[Enrichment] | None = Field(
        default=None,
        description='The additional information from an external data source, which is associated with the event or a finding. For example add location information for the IP address in the DNS answers:</p><code>[{"name": "answers.ip", "value": "92.24.47.250", "type": "location", "data": {"city": "Socotra", "continent": "Asia", "coordinates": [-25.4153, 17.0743], "country": "YE", "desc": "Yemen"}}]</code>',
    )
    file: File | None = Field(
        default=None,
        description="The file <p style='display:inline;color:red'>targeted by</p> the activity. Example: <code>/var/log/audit.log</code> [Recommended]",
    )
    include: str | None = Field(default=None, description="")
    log_name: str | None = Field(
        default=None,
        description="The name of the event log <p style='display:inline;color:red'>targeted by</p> the activity. Example: Windows <code>Security</code>. [Recommended]",
    )
    log_provider: str | None = Field(
        default=None,
        description="The logging provider or logging service <p style='display:inline;color:red'>targeted by</p> the activity.<br />Example: <code>Microsoft-Windows-Security-Auditing</code>, <code>Auditd</code>, or <code>Syslog</code>. [Recommended]",
    )
    log_type: str | None = Field(
        default=None,
        description="The log type, normalized to the caption of the <code>log_type_id</code> value. In the case of 'Other', it is defined by the event source. [Recommended]",
    )
    log_type_id: LogTypeId | None = Field(
        default=None, description="The normalized log type identifier. [Recommended]"
    )
    message: str | None = Field(
        default=None,
        description="The description of the event/finding, as defined by the source. [Recommended]",
    )
    observables: list[Observable] | None = Field(
        default=None,
        description="The observables associated with the event or a finding. [Recommended]",
    )
    raw_data: str | None = Field(
        default=None, description="The raw event/finding data as received from the source."
    )
    raw_data_size: int | None = Field(
        default=None,
        description="The size of the raw data which was transformed into an OCSF event, in bytes.",
    )
    severity: str | None = Field(
        default=None,
        description="The event/finding severity, normalized to the caption of the <code>severity_id</code> value. In the case of 'Other', it is defined by the source.",
    )
    src_endpoint: NetworkEndpoint | None = Field(
        default=None, description="The source endpoint for the event log activity. [Recommended]"
    )
    start_time: int | None = Field(
        default=None,
        description="The start time of a time period, or the time of the least recent event included in the aggregate event.",
    )
    status: str | None = Field(
        default=None,
        description="The event status, normalized to the caption of the status_id value. In the case of 'Other', it is defined by the event source. [Recommended]",
    )
    status_code: str | None = Field(
        default=None,
        description="The event status code, as reported by the event source.<br />Example: <code>0</code>, <code>8</code>, or <code>21</code> for <a target='_blank' href='https://learn.microsoft.com/en-us/previous-versions/windows/desktop/eventlogprov/cleareventlog-method-in-class-win32-nteventlogfile'>Windows ClearEventLog</a>. [Recommended]",
    )
    status_detail: str | None = Field(
        default=None,
        description="The status detail contains additional information about the event outcome.<br />Example: <code>Success</code>, <code>Privilege Missing</code>, or <code>Invalid Parameter</code> for <a target='_blank' href='https://learn.microsoft.com/en-us/previous-versions/windows/desktop/eventlogprov/cleareventlog-method-in-class-win32-nteventlogfile'>Windows ClearEventLog</a>. [Recommended]",
    )
    status_id: StatusId | None = Field(
        default=None, description="The normalized identifier of the event status. [Recommended]"
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
