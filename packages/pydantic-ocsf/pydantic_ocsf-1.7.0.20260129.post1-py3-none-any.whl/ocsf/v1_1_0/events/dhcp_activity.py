"""DHCP Activity event class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_1_0.enums.activity_id import ActivityId
    from ocsf.v1_1_0.enums.severity_id import SeverityId
    from ocsf.v1_1_0.enums.status_id import StatusId
    from ocsf.v1_1_0.objects.enrichment import Enrichment
    from ocsf.v1_1_0.objects.metadata import Metadata
    from ocsf.v1_1_0.objects.network_connection_info import NetworkConnectionInfo
    from ocsf.v1_1_0.objects.network_endpoint import NetworkEndpoint
    from ocsf.v1_1_0.objects.network_interface import NetworkInterface
    from ocsf.v1_1_0.objects.network_proxy import NetworkProxy
    from ocsf.v1_1_0.objects.network_traffic import NetworkTraffic
    from ocsf.v1_1_0.objects.object import Object
    from ocsf.v1_1_0.objects.observable import Observable
    from ocsf.v1_1_0.objects.tls import Tls


class DhcpActivity(OCSFBaseModel):
    """DHCP Activity events report MAC to IP assignment via DHCP from a client or server.

    OCSF Class UID: 4
    Category: network

    See: https://schema.ocsf.io/1.1.0/classes/dhcp_activity
    """

    # Class identifiers
    class_uid: Literal[4] = Field(
        default=4, description="The unique identifier of the event class."
    )
    category_uid: Literal[0] = Field(default=0, description="The category unique identifier.")
    activity_id: ActivityId = Field(
        ..., description="The normalized identifier of the activity that triggered the event."
    )
    metadata: Metadata = Field(
        ..., description="The metadata associated with the event or a finding."
    )
    severity_id: SeverityId = Field(
        ...,
        description="<p>The normalized identifier of the event/finding severity.</p>The normalized severity is a measurement the effort and expense required to manage and resolve an event or incident. Smaller numerical values represent lower impact events, and larger numerical values represent higher impact events.",
    )
    app_name: str | None = Field(
        default=None,
        description="The name of the application that is associated with the event or object.",
    )
    connection_info: NetworkConnectionInfo | None = Field(
        default=None, description="The network connection information. [Recommended]"
    )
    dst_endpoint: NetworkEndpoint | None = Field(
        default=None, description="The responder (server) of the DHCP connection. [Recommended]"
    )
    enrichments: list[Enrichment] | None = Field(
        default=None,
        description='The additional information from an external data source, which is associated with the event or a finding. For example add location information for the IP address in the DNS answers:</p><code>[{"name": "answers.ip", "value": "92.24.47.250", "type": "location", "data": {"city": "Socotra", "continent": "Asia", "coordinates": [-25.4153, 17.0743], "country": "YE", "desc": "Yemen"}}]</code>',
    )
    include: str | None = Field(default=None, description="")
    is_renewal: bool | None = Field(
        default=None, description="The indication of whether this is a lease/session renewal event."
    )
    lease_dur: int | None = Field(
        default=None,
        description="This represents the length of the DHCP lease in seconds. This is present in DHCP Ack events.",
    )
    message: str | None = Field(
        default=None,
        description="The description of the event/finding, as defined by the source. [Recommended]",
    )
    observables: list[Observable] | None = Field(
        default=None, description="The observables associated with the event or a finding."
    )
    proxy: NetworkProxy | None = Field(
        default=None, description="The proxy (server) in a network connection."
    )
    raw_data: str | None = Field(
        default=None, description="The raw event/finding data as received from the source."
    )
    relay: NetworkInterface | None = Field(
        default=None, description="The network relay that is associated with the event."
    )
    severity: str | None = Field(
        default=None,
        description="The event/finding severity, normalized to the caption of the severity_id value. In the case of 'Other', it is defined by the source.",
    )
    src_endpoint: NetworkEndpoint | None = Field(
        default=None, description="The initiator (client) of the DHCP connection. [Recommended]"
    )
    status: str | None = Field(
        default=None,
        description="The event status, normalized to the caption of the status_id value. In the case of 'Other', it is defined by the event source.",
    )
    status_code: str | None = Field(
        default=None,
        description="The event status code, as reported by the event source.<br /><br />For example, in a Windows Failed Authentication event, this would be the value of 'Failure Code', e.g. 0x18.",
    )
    status_detail: str | None = Field(
        default=None,
        description="The status details contains additional information about the event/finding outcome.",
    )
    status_id: StatusId | None = Field(
        default=None, description="The normalized identifier of the event status. [Recommended]"
    )
    tls: Tls | None = Field(
        default=None, description="The Transport Layer Security (TLS) attributes."
    )
    traffic: NetworkTraffic | None = Field(
        default=None,
        description="The network traffic refers to the amount of data moving across a network at a given point of time. Intended to be used alongside Network Connection.",
    )
    transaction_uid: str | None = Field(
        default=None,
        description="The unique identifier of the transaction. This is typically a random number generated from the client to associate a dhcp request/response pair.",
    )
    unmapped: Object | None = Field(
        default=None,
        description="The attributes that are not mapped to the event schema. The names and values of those attributes are specific to the event source.",
    )
