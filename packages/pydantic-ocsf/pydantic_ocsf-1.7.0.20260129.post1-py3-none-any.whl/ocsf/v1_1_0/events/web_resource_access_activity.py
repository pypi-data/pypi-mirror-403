"""Web Resource Access Activity event class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_1_0.enums.activity_id import ActivityId
    from ocsf.v1_1_0.enums.severity_id import SeverityId
    from ocsf.v1_1_0.enums.status_id import StatusId
    from ocsf.v1_1_0.objects.enrichment import Enrichment
    from ocsf.v1_1_0.objects.http_request import HttpRequest
    from ocsf.v1_1_0.objects.http_response import HttpResponse
    from ocsf.v1_1_0.objects.metadata import Metadata
    from ocsf.v1_1_0.objects.network_endpoint import NetworkEndpoint
    from ocsf.v1_1_0.objects.network_proxy import NetworkProxy
    from ocsf.v1_1_0.objects.object import Object
    from ocsf.v1_1_0.objects.observable import Observable
    from ocsf.v1_1_0.objects.tls import Tls
    from ocsf.v1_1_0.objects.web_resource import WebResource


class WebResourceAccessActivity(OCSFBaseModel):
    """Web Resource Access Activity events describe successful/failed attempts to access a web resource over HTTP.

    OCSF Class UID: 4
    Category: application

    See: https://schema.ocsf.io/1.1.0/classes/web_resource_access_activity
    """

    # Class identifiers
    class_uid: Literal[4] = Field(
        default=4, description="The unique identifier of the event class."
    )
    category_uid: Literal[0] = Field(default=0, description="The category unique identifier.")
    http_request: HttpRequest = Field(..., description="Details about the underlying HTTP request.")
    metadata: Metadata = Field(
        ..., description="The metadata associated with the event or a finding."
    )
    severity_id: SeverityId = Field(
        ...,
        description="<p>The normalized identifier of the event/finding severity.</p>The normalized severity is a measurement the effort and expense required to manage and resolve an event or incident. Smaller numerical values represent lower impact events, and larger numerical values represent higher impact events.",
    )
    web_resources: list[WebResource] = Field(
        ..., description="Details about the resource that is the target of the activity."
    )
    activity_id: ActivityId | None = Field(
        default=None,
        description="The normalized identifier of the activity that triggered the event.",
    )
    enrichments: list[Enrichment] | None = Field(
        default=None,
        description='The additional information from an external data source, which is associated with the event or a finding. For example add location information for the IP address in the DNS answers:</p><code>[{"name": "answers.ip", "value": "92.24.47.250", "type": "location", "data": {"city": "Socotra", "continent": "Asia", "coordinates": [-25.4153, 17.0743], "country": "YE", "desc": "Yemen"}}]</code>',
    )
    http_response: HttpResponse | None = Field(
        default=None, description="Details about the HTTP response, if available."
    )
    include: str | None = Field(default=None, description="")
    message: str | None = Field(
        default=None,
        description="The description of the event/finding, as defined by the source. [Recommended]",
    )
    observables: list[Observable] | None = Field(
        default=None, description="The observables associated with the event or a finding."
    )
    proxy: NetworkProxy | None = Field(
        default=None, description="Details about the proxy service, if available."
    )
    raw_data: str | None = Field(
        default=None, description="The raw event/finding data as received from the source."
    )
    severity: str | None = Field(
        default=None,
        description="The event/finding severity, normalized to the caption of the severity_id value. In the case of 'Other', it is defined by the source.",
    )
    src_endpoint: NetworkEndpoint | None = Field(
        default=None, description="Details about the source endpoint of the request. [Recommended]"
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
        default=None, description="The Transport Layer Security (TLS) attributes, if available."
    )
    unmapped: Object | None = Field(
        default=None,
        description="The attributes that are not mapped to the event schema. The names and values of those attributes are specific to the event source.",
    )
