"""NTP Activity event class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_2_0.enums.activity_id import ActivityId
    from ocsf.v1_2_0.enums.severity_id import SeverityId
    from ocsf.v1_2_0.enums.status_id import StatusId
    from ocsf.v1_2_0.enums.stratum_id import StratumId
    from ocsf.v1_2_0.objects.enrichment import Enrichment
    from ocsf.v1_2_0.objects.metadata import Metadata
    from ocsf.v1_2_0.objects.network_connection_info import NetworkConnectionInfo
    from ocsf.v1_2_0.objects.network_endpoint import NetworkEndpoint
    from ocsf.v1_2_0.objects.network_proxy import NetworkProxy
    from ocsf.v1_2_0.objects.network_traffic import NetworkTraffic
    from ocsf.v1_2_0.objects.object import Object
    from ocsf.v1_2_0.objects.observable import Observable
    from ocsf.v1_2_0.objects.tls import Tls


class NtpActivity(OCSFBaseModel):
    """The Network Time Protocol (NTP) Activity events report instances of remote clients synchronizing their clocks with an NTP server, as observed on the network.

    OCSF Class UID: 13
    Category:

    See: https://schema.ocsf.io/1.2.0/classes/ntp_activity
    """

    # Class identifiers
    class_uid: Literal[13] = Field(
        default=13, description="The unique identifier of the event class."
    )
    category_uid: Literal[0] = Field(default=0, description="The category unique identifier.")
    dst_endpoint: NetworkEndpoint = Field(
        ..., description="The responder (server) in a network connection."
    )
    metadata: Metadata = Field(
        ..., description="The metadata associated with the event or a finding."
    )
    severity_id: SeverityId = Field(
        ...,
        description="<p>The normalized identifier of the event/finding severity.</p>The normalized severity is a measurement the effort and expense required to manage and resolve an event or incident. Smaller numerical values represent lower impact events, and larger numerical values represent higher impact events.",
    )
    src_endpoint: NetworkEndpoint = Field(
        ..., description="The initiator (client) of the network connection."
    )
    version: str = Field(..., description="The version number of the NTP protocol.")
    activity_id: ActivityId | None = Field(
        default=None,
        description="The normalized identifier of the activity that triggered the event.",
    )
    app_name: str | None = Field(
        default=None, description="The name of the application associated with the event or object."
    )
    connection_info: NetworkConnectionInfo | None = Field(
        default=None, description="The network connection information. [Recommended]"
    )
    delay: int | None = Field(
        default=None,
        description="The total round-trip delay to the reference clock in milliseconds. [Recommended]",
    )
    dispersion: int | None = Field(
        default=None,
        description="The dispersion in the NTP protocol is the estimated time error or uncertainty relative to the reference clock in milliseconds. [Recommended]",
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
    precision: int | None = Field(
        default=None,
        description="The NTP precision quantifies a clock's accuracy and stability in log2 seconds, as defined in RFC-5905. [Recommended]",
    )
    proxy: NetworkProxy | None = Field(
        default=None, description="The proxy (server) in a network connection. [Recommended]"
    )
    raw_data: str | None = Field(
        default=None, description="The raw event/finding data as received from the source."
    )
    severity: str | None = Field(
        default=None,
        description="The event/finding severity, normalized to the caption of the severity_id value. In the case of 'Other', it is defined by the source.",
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
        description="The status details contains additional information about the event/finding outcome. [Recommended]",
    )
    status_id: StatusId | None = Field(
        default=None, description="The normalized identifier of the event status. [Recommended]"
    )
    stratum: str | None = Field(
        default=None,
        description="The stratum level of the NTP server's time source, normalized to the caption of the stratum_id value. [Recommended]",
    )
    stratum_id: StratumId | None = Field(
        default=None,
        description="The normalized identifier of the stratum level, as defined in <a target='_blank' href='https://www.rfc-editor.org/rfc/rfc5905.html'>RFC-5905</a>. [Recommended]",
    )
    tls: Tls | None = Field(
        default=None, description="The Transport Layer Security (TLS) attributes."
    )
    traffic: NetworkTraffic | None = Field(
        default=None,
        description="The network traffic refers to the amount of data moving across a network at a given point of time. Intended to be used alongside Network Connection. [Recommended]",
    )
    unmapped: Object | None = Field(
        default=None,
        description="The attributes that are not mapped to the event schema. The names and values of those attributes are specific to the event source.",
    )
