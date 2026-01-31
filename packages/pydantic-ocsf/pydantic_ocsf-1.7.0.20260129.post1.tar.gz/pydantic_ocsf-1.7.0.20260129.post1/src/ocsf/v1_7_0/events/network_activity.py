"""Network Activity event class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.enums.activity_id import ActivityId
    from ocsf.v1_7_0.enums.observation_point_id import ObservationPointId
    from ocsf.v1_7_0.enums.severity_id import SeverityId
    from ocsf.v1_7_0.enums.status_id import StatusId
    from ocsf.v1_7_0.objects.enrichment import Enrichment
    from ocsf.v1_7_0.objects.fingerprint import Fingerprint
    from ocsf.v1_7_0.objects.ja4_fingerprint import Ja4Fingerprint
    from ocsf.v1_7_0.objects.metadata import Metadata
    from ocsf.v1_7_0.objects.network_connection_info import NetworkConnectionInfo
    from ocsf.v1_7_0.objects.network_endpoint import NetworkEndpoint
    from ocsf.v1_7_0.objects.network_proxy import NetworkProxy
    from ocsf.v1_7_0.objects.network_traffic import NetworkTraffic
    from ocsf.v1_7_0.objects.object import Object
    from ocsf.v1_7_0.objects.observable import Observable
    from ocsf.v1_7_0.objects.tls import Tls
    from ocsf.v1_7_0.objects.url import Url


class NetworkActivity(OCSFBaseModel):
    """Network Activity events report network connection and traffic activity.

    OCSF Class UID: 1
    Category:

    See: https://schema.ocsf.io/1.7.0/classes/network_activity
    """

    # Class identifiers
    class_uid: Literal[1] = Field(
        default=1, description="The unique identifier of the event class."
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
    app_name: str | None = Field(
        default=None, description="The name of the application associated with the event or object."
    )
    category_name: str | None = Field(
        default=None, description="The event category name, as defined by category_uid value."
    )
    class_name: str | None = Field(
        default=None, description="The event class name, as defined by class_uid value."
    )
    connection_info: NetworkConnectionInfo | None = Field(
        default=None, description="The network connection information. [Recommended]"
    )
    count: int | None = Field(
        default=None,
        description="The number of times that events in the same logical group occurred during the event <strong>Start Time</strong> to <strong>End Time</strong> period.",
    )
    cumulative_traffic: NetworkTraffic | None = Field(
        default=None,
        description="The cumulative (running total) network traffic aggregated from the start of a flow or session. Use when reporting: (1) total accumulated bytes/packets since flow initiation, (2) combined aggregation models where both incremental deltas and running totals are reported together (populate both <code>traffic</code> for the delta and this attribute for the cumulative total), or (3) final summary metrics when a long-lived connection closes. This represents the sum of all activity from flow start to the current observation, not a delta or point-in-time value.",
    )
    dst_endpoint: NetworkEndpoint | None = Field(
        default=None,
        description="The responder of the network connection. In some contexts an event source cannot correctly identify the responder. Refer to <code>is_src_dst_assignment_known</code> for certainty.",
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
    include: str | None = Field(default=None, description="")
    is_src_dst_assignment_known: bool | None = Field(
        default=None,
        description="<code>true</code> denotes that <code>src_endpoint</code> and <code>dst_endpoint</code> correctly identify the initiator and responder respectively. <code>false</code> denotes that the event source has arbitrarily assigned one peer to <code>src_endpoint</code> and the other to <code>dst_endpoint</code>, in other words that initiator and responder are not being asserted. This can occur, for example, when the event source is a network appliance that has not observed the initiation of a given connection. In the absence of this attribute, interpretation of the initiator and responder is implementation-specific. [Recommended]",
    )
    ja4_fingerprint_list: list[Ja4Fingerprint] | None = Field(
        default=None, description="A list of the JA4+ network fingerprints."
    )
    message: str | None = Field(
        default=None,
        description="The description of the event/finding, as defined by the source. [Recommended]",
    )
    observables: list[Observable] | None = Field(
        default=None,
        description="The observables associated with the event or a finding. [Recommended]",
    )
    observation_point: str | None = Field(
        default=None,
        description="Indicates whether the source network endpoint, destination network endpoint, or neither served as the observation point for the activity. The value is normalized to the caption of the <code>observation_point_id</code>.",
    )
    observation_point_id: ObservationPointId | None = Field(
        default=None,
        description="The normalized identifier of the observation point. The observation point identifier indicates whether the source network endpoint, destination network endpoint, or neither served as the observation point for the activity.",
    )
    proxy: NetworkProxy | None = Field(
        default=None, description="The proxy (server) in a network connection. [Recommended]"
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
    src_endpoint: NetworkEndpoint | None = Field(
        default=None,
        description=" The initiator of the network connection. In some contexts an event source cannot correctly identify the initiator. Refer to <code>is_src_dst_assignment_known</code> for certainty.",
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
    tls: Tls | None = Field(
        default=None, description="The Transport Layer Security (TLS) attributes."
    )
    traffic: NetworkTraffic | None = Field(
        default=None,
        description="The network traffic for this observation period. Use when reporting: (1) delta values (bytes/packets transferred since the last observation), (2) instantaneous measurements at a specific point in time, or (3) standalone single-event metrics. This attribute represents a point-in-time measurement or incremental change, not a running total. For accumulated totals across multiple observations or the lifetime of a flow, use <code>cumulative_traffic</code> instead. [Recommended]",
    )
    type_name: str | None = Field(
        default=None, description="The event/finding type name, as defined by the type_uid."
    )
    unmapped: Object | None = Field(
        default=None,
        description="The attributes that are not mapped to the event schema. The names and values of those attributes are specific to the event source.",
    )
    url: Url | None = Field(
        default=None, description="The URL details relevant to the network traffic. [Recommended]"
    )
