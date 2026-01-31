"""Drone Flights Activity event class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.activity_id import ActivityId
    from ocsf.v1_5_0.enums.auth_protocol_id import AuthProtocolId
    from ocsf.v1_5_0.enums.severity_id import SeverityId
    from ocsf.v1_5_0.enums.status_id import StatusId
    from ocsf.v1_5_0.objects.enrichment import Enrichment
    from ocsf.v1_5_0.objects.metadata import Metadata
    from ocsf.v1_5_0.objects.network_connection_info import NetworkConnectionInfo
    from ocsf.v1_5_0.objects.network_endpoint import NetworkEndpoint
    from ocsf.v1_5_0.objects.network_proxy import NetworkProxy
    from ocsf.v1_5_0.objects.network_traffic import NetworkTraffic
    from ocsf.v1_5_0.objects.object import Object
    from ocsf.v1_5_0.objects.observable import Observable
    from ocsf.v1_5_0.objects.tls import Tls
    from ocsf.v1_5_0.objects.unmanned_aerial_system import UnmannedAerialSystem
    from ocsf.v1_5_0.objects.unmanned_system_operating_area import UnmannedSystemOperatingArea
    from ocsf.v1_5_0.objects.user import User


class DroneFlightsActivity(OCSFBaseModel):
    """Drone Flights Activity events report the activity of Unmanned Aerial Systems (UAS), their Operators, and mission-planning and authorization metadata as reported by the UAS platforms themselves, by Counter-UAS (CUAS) systems, or other remote monitoring or sensing infrastructure. Based on the Remote ID defined in Standard Specification for Remote ID and Tracking (ASTM Designation: F3411-22a) <a target='_blank' href='https://cdn.standards.iteh.ai/samples/112830/71297057ac42432880a203654f213709/ASTM-F3411-22a.pdf'>ASTM F3411-22a</a>

    OCSF Class UID: 1
    Category:

    See: https://schema.ocsf.io/1.5.0/classes/drone_flights_activity
    """

    # Class identifiers
    class_uid: Literal[1] = Field(
        default=1, description="The unique identifier of the event class."
    )
    category_uid: Literal[0] = Field(default=0, description="The category unique identifier.")
    activity_id: ActivityId = Field(
        ..., description="The normalized identifier of the activity that triggered the event."
    )
    dst_endpoint: NetworkEndpoint = Field(
        ...,
        description="The destination network endpoint of the Unmanned Aerial System (UAS), Counter Unmanned Aerial System (CUAS) platform, or other unmanned systems monitoring and/or sensing infrastructure.",
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
    unmanned_aerial_system: UnmannedAerialSystem = Field(
        ...,
        description="The Unmanned Aerial System object describes the characteristics, Position Location Information (PLI), and other metadata of Unmanned Aerial Systems (UAS) and other unmanned and drone systems used in Remote ID. Remote ID is defined in the Standard Specification for Remote ID and Tracking (ASTM Designation: F3411-22a) <a target='_blank' href='https://cdn.standards.iteh.ai/samples/112830/71297057ac42432880a203654f213709/ASTM-F3411-22a.pdf'>ASTM F3411-22a</a>.",
    )
    unmanned_system_operator: User = Field(
        ..., description="The human or machine operator of an Unmanned System."
    )
    activity_name: str | None = Field(
        default=None, description="The event activity name, as defined by the activity_id."
    )
    auth_protocol: str | None = Field(
        default=None,
        description="The authentication type as defined by the caption of <code>auth_protocol_id</code>. In the case of 'Other', it is defined by the event source.",
    )
    auth_protocol_id: AuthProtocolId | None = Field(
        default=None,
        description="The normalized identifier of the authentication type used to authorize a flight plan or mission.",
    )
    category_name: str | None = Field(
        default=None, description="The event category name, as defined by category_uid value."
    )
    class_name: str | None = Field(
        default=None, description="The event class name, as defined by class_uid value."
    )
    classification: str | None = Field(
        default=None,
        description="UA Classification - Allows a region to classify UAS in a regional specific manner. The format may differ from region to region.",
    )
    comment: str | None = Field(
        default=None,
        description="This optional, free-text field enables the operator to describe the purpose of a flight, if so desired.",
    )
    connection_info: NetworkConnectionInfo | None = Field(
        default=None, description="The network connection information. [Recommended]"
    )
    count: int | None = Field(
        default=None,
        description="The number of times that events in the same logical group occurred during the event <strong>Start Time</strong> to <strong>End Time</strong> period.",
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
    message: str | None = Field(
        default=None,
        description="The description of the event/finding, as defined by the source. [Recommended]",
    )
    observables: list[Observable] | None = Field(
        default=None,
        description="The observables associated with the event or a finding. [Recommended]",
    )
    protocol_name: str | None = Field(
        default=None,
        description="The networking protocol associated with the Remote ID device or beacon. E.g. <code>BLE</code>, <code>LTE</code>, <code>802.11</code>.",
    )
    proxy_endpoint: NetworkProxy | None = Field(
        default=None, description="The proxy (server) in a network connection. [Recommended]"
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
        default=None, description="The network source endpoint."
    )
    start_time: int | None = Field(
        default=None,
        description="The start time of a time period, or the time of the least recent event included in the aggregate event.",
    )
    status: str | None = Field(
        default=None,
        description="The normalized Operational status for the Unmanned Aerial System (UAS) normalized to the caption of the <code>status_id</code> value. In the case of 'Other', it is defined by the source.",
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
        description="The normalized Operational status identifier for the Unmanned Aerial System (UAS). [Recommended]",
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
        description="Traffic refers to the amount of data transmitted from a Unmanned Aerial System (UAS) or Counter Unmanned Aerial System (UAS) (CUAS) system at a given point of time. Ex: <code>bytes_in</code> and <code>bytes_out</code>.",
    )
    type_name: str | None = Field(
        default=None, description="The event/finding type name, as defined by the type_uid."
    )
    unmanned_system_operating_area: UnmannedSystemOperatingArea | None = Field(
        default=None,
        description="The UAS Operating Area object describes details about a precise area of operations for a UAS flight or mission. [Recommended]",
    )
    unmapped: Object | None = Field(
        default=None,
        description="The attributes that are not mapped to the event schema. The names and values of those attributes are specific to the event source.",
    )
