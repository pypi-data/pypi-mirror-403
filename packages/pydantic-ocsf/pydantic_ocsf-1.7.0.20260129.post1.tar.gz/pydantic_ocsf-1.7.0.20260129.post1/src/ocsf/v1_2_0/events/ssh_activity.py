"""SSH Activity event class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_2_0.enums.auth_type_id import AuthTypeId
    from ocsf.v1_2_0.enums.severity_id import SeverityId
    from ocsf.v1_2_0.enums.status_id import StatusId
    from ocsf.v1_2_0.objects.enrichment import Enrichment
    from ocsf.v1_2_0.objects.file import File
    from ocsf.v1_2_0.objects.hassh import Hassh
    from ocsf.v1_2_0.objects.metadata import Metadata
    from ocsf.v1_2_0.objects.network_connection_info import NetworkConnectionInfo
    from ocsf.v1_2_0.objects.network_endpoint import NetworkEndpoint
    from ocsf.v1_2_0.objects.network_proxy import NetworkProxy
    from ocsf.v1_2_0.objects.network_traffic import NetworkTraffic
    from ocsf.v1_2_0.objects.object import Object
    from ocsf.v1_2_0.objects.observable import Observable
    from ocsf.v1_2_0.objects.tls import Tls


class SshActivity(OCSFBaseModel):
    """SSH Activity events report remote client connections to a server using the Secure Shell (SSH) Protocol.

    OCSF Class UID: 7
    Category:

    See: https://schema.ocsf.io/1.2.0/classes/ssh_activity
    """

    # Class identifiers
    class_uid: Literal[7] = Field(
        default=7, description="The unique identifier of the event class."
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
    app_name: str | None = Field(
        default=None, description="The name of the application associated with the event or object."
    )
    auth_type: str | None = Field(
        default=None,
        description="The SSH authentication type, normalized to the caption of 'auth_type_id'. In the case of 'Other', it is defined by the event source. [Recommended]",
    )
    auth_type_id: AuthTypeId | None = Field(
        default=None,
        description="The normalized identifier of the SSH authentication type. [Recommended]",
    )
    client_hassh: Hassh | None = Field(
        default=None, description="The Client HASSH fingerprinting object. [Recommended]"
    )
    connection_info: NetworkConnectionInfo | None = Field(
        default=None, description="The network connection information. [Recommended]"
    )
    enrichments: list[Enrichment] | None = Field(
        default=None,
        description='The additional information from an external data source, which is associated with the event or a finding. For example add location information for the IP address in the DNS answers:</p><code>[{"name": "answers.ip", "value": "92.24.47.250", "type": "location", "data": {"city": "Socotra", "continent": "Asia", "coordinates": [-25.4153, 17.0743], "country": "YE", "desc": "Yemen"}}]</code>',
    )
    file: File | None = Field(
        default=None, description="The file that is the target of the SSH activity."
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
    protocol_ver: str | None = Field(
        default=None, description="The Secure Shell Protocol version. [Recommended]"
    )
    proxy: NetworkProxy | None = Field(
        default=None, description="The proxy (server) in a network connection. [Recommended]"
    )
    raw_data: str | None = Field(
        default=None, description="The raw event/finding data as received from the source."
    )
    server_hassh: Hassh | None = Field(
        default=None, description="The Server HASSH fingerprinting object. [Recommended]"
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
