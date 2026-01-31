"""Tunnel Activity event class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_2_0.enums.activity_id import ActivityId
    from ocsf.v1_2_0.enums.severity_id import SeverityId
    from ocsf.v1_2_0.enums.status_id import StatusId
    from ocsf.v1_2_0.enums.tunnel_type_id import TunnelTypeId
    from ocsf.v1_2_0.objects.device import Device
    from ocsf.v1_2_0.objects.enrichment import Enrichment
    from ocsf.v1_2_0.objects.metadata import Metadata
    from ocsf.v1_2_0.objects.network_connection_info import NetworkConnectionInfo
    from ocsf.v1_2_0.objects.network_endpoint import NetworkEndpoint
    from ocsf.v1_2_0.objects.network_interface import NetworkInterface
    from ocsf.v1_2_0.objects.network_proxy import NetworkProxy
    from ocsf.v1_2_0.objects.network_traffic import NetworkTraffic
    from ocsf.v1_2_0.objects.object import Object
    from ocsf.v1_2_0.objects.observable import Observable
    from ocsf.v1_2_0.objects.session import Session
    from ocsf.v1_2_0.objects.tls import Tls
    from ocsf.v1_2_0.objects.user import User


class TunnelActivity(OCSFBaseModel):
    """Tunnel Activity events report secure tunnel establishment (such as VPN), teardowns, renewals, and other network tunnel specific actions.

    OCSF Class UID: 14
    Category: network

    See: https://schema.ocsf.io/1.2.0/classes/tunnel_activity
    """

    # Class identifiers
    class_uid: Literal[14] = Field(
        default=14, description="The unique identifier of the event class."
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
        default=None, description="The name of the application associated with the event or object."
    )
    connection_info: NetworkConnectionInfo | None = Field(
        default=None, description="The tunnel connection information."
    )
    device: Device | None = Field(
        default=None, description="The device that reported the event. [Recommended]"
    )
    dst_endpoint: NetworkEndpoint | None = Field(
        default=None, description="The server responding to the tunnel connection. [Recommended]"
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
        description="The networking protocol associated with the tunnel. E.g. <code>IPSec</code>, <code>SSL</code>, <code>GRE</code>.",
    )
    proxy: NetworkProxy | None = Field(
        default=None, description="The proxy (server) in a network connection. [Recommended]"
    )
    raw_data: str | None = Field(
        default=None, description="The raw event/finding data as received from the source."
    )
    session: Session | None = Field(
        default=None, description="The session associated with the tunnel. [Recommended]"
    )
    severity: str | None = Field(
        default=None,
        description="The event/finding severity, normalized to the caption of the severity_id value. In the case of 'Other', it is defined by the source.",
    )
    src_endpoint: NetworkEndpoint | None = Field(
        default=None, description="The initiator (client) of the tunnel connection. [Recommended]"
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
    tls: Tls | None = Field(
        default=None, description="The Transport Layer Security (TLS) attributes."
    )
    traffic: NetworkTraffic | None = Field(
        default=None,
        description="Traffic refers to the amount of data moving across the tunnel at a given point of time. Ex: <code>bytes_in</code> and <code>bytes_out</code>.",
    )
    tunnel_interface: NetworkInterface | None = Field(
        default=None,
        description="The information about the virtual tunnel interface, e.g. <code>utun0</code>. This is usually associated with the private (rfc-1918) ip of the tunnel. [Recommended]",
    )
    tunnel_type: str | None = Field(
        default=None,
        description="The tunnel type. Example: <code>Split</code> or <code>Full</code>. [Recommended]",
    )
    tunnel_type_id: TunnelTypeId | None = Field(
        default=None, description="The normalized tunnel type ID. [Recommended]"
    )
    unmapped: Object | None = Field(
        default=None,
        description="The attributes that are not mapped to the event schema. The names and values of those attributes are specific to the event source.",
    )
    user: User | None = Field(
        default=None, description="The user associated with the tunnel activity. [Recommended]"
    )
