"""RDP Activity event class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_0_0.enums.activity_id import ActivityId
    from ocsf.v1_0_0.enums.severity_id import SeverityId
    from ocsf.v1_0_0.enums.status_id import StatusId
    from ocsf.v1_0_0.objects.device import Device
    from ocsf.v1_0_0.objects.display import Display
    from ocsf.v1_0_0.objects.enrichment import Enrichment
    from ocsf.v1_0_0.objects.metadata import Metadata
    from ocsf.v1_0_0.objects.object import Object
    from ocsf.v1_0_0.objects.observable import Observable
    from ocsf.v1_0_0.objects.request import Request
    from ocsf.v1_0_0.objects.response import Response


class RdpActivity(OCSFBaseModel):
    """Remote Desktop Protocol (RDP) Activity events report remote client connections to a server as seen on the network.

    OCSF Class UID: 5
    Category:

    See: https://schema.ocsf.io/1.0.0/classes/rdp_activity
    """

    # Class identifiers
    class_uid: Literal[5] = Field(
        default=5, description="The unique identifier of the event class."
    )
    category_uid: Literal[0] = Field(default=0, description="The category unique identifier.")
    metadata: Metadata = Field(..., description="The metadata associated with the event.")
    severity_id: SeverityId = Field(
        ...,
        description="<p>The normalized identifier of the event severity.</p>The normalized severity is a measurement the effort and expense required to manage and resolve an event or incident. Smaller numerical values represent lower impact events, and larger numerical values represent higher impact events.",
    )
    activity_id: ActivityId | None = Field(
        default=None,
        description="The normalized identifier of the activity that triggered the event.",
    )
    capabilities: list[str] | None = Field(default=None, description="A list of RDP capabilities.")
    certificate_chain: list[str] | None = Field(
        default=None, description="The list of observed certificates in an RDP TLS connection."
    )
    device: Device | None = Field(
        default=None, description="The device instigating the RDP connection."
    )
    enrichments: list[Enrichment] | None = Field(
        default=None,
        description='The additional information from an external data source, which is associated with the event. For example add location information for the IP address in the DNS answers:</p><code>[{"name": "answers.ip", "value": "92.24.47.250", "type": "location", "data": {"city": "Socotra", "continent": "Asia", "coordinates": [-25.4153, 17.0743], "country": "YE", "desc": "Yemen"}}]</code>',
    )
    identifier_cookie: str | None = Field(
        default=None, description="The client identifier cookie during client/server exchange."
    )
    include: str | None = Field(default=None, description="")
    message: str | None = Field(
        default=None,
        description="The description of the event, as defined by the event source. [Recommended]",
    )
    observables: list[Observable] | None = Field(
        default=None, description="The observables associated with the event."
    )
    protocol_ver: str | None = Field(
        default=None, description="The Remote Desktop Protocol version. [Recommended]"
    )
    raw_data: str | None = Field(
        default=None, description="The event data as received from the event source."
    )
    remote_display: Display | None = Field(
        default=None, description="The remote display affiliated with the event"
    )
    request: Request | None = Field(
        default=None, description="The client request in an RDP network connection. [Recommended]"
    )
    response: Response | None = Field(
        default=None, description="The server response in an RDP network connection. [Recommended]"
    )
    severity: str | None = Field(
        default=None,
        description="The event severity, normalized to the caption of the severity_id value. In the case of 'Other', it is defined by the event source.",
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
        description="The status details contains additional information about the event outcome.",
    )
    status_id: StatusId | None = Field(
        default=None, description="The normalized identifier of the event status. [Recommended]"
    )
    unmapped: Object | None = Field(
        default=None,
        description="The attributes that are not mapped to the event schema. The names and values of those attributes are specific to the event source.",
    )
