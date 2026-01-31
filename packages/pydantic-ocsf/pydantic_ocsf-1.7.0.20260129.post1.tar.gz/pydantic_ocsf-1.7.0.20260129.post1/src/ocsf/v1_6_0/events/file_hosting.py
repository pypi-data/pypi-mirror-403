"""File Hosting Activity event class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.enums.activity_id import ActivityId
    from ocsf.v1_6_0.enums.severity_id import SeverityId
    from ocsf.v1_6_0.enums.share_type_id import ShareTypeId
    from ocsf.v1_6_0.enums.status_id import StatusId
    from ocsf.v1_6_0.objects.actor import Actor
    from ocsf.v1_6_0.objects.enrichment import Enrichment
    from ocsf.v1_6_0.objects.file import File
    from ocsf.v1_6_0.objects.fingerprint import Fingerprint
    from ocsf.v1_6_0.objects.http_request import HttpRequest
    from ocsf.v1_6_0.objects.http_response import HttpResponse
    from ocsf.v1_6_0.objects.metadata import Metadata
    from ocsf.v1_6_0.objects.network_connection_info import NetworkConnectionInfo
    from ocsf.v1_6_0.objects.network_endpoint import NetworkEndpoint
    from ocsf.v1_6_0.objects.object import Object
    from ocsf.v1_6_0.objects.observable import Observable


class FileHosting(OCSFBaseModel):
    """File Hosting Activity events report the actions taken by file management applications, including file sharing servers like Sharepoint and services such as Box, MS OneDrive, Google Drive, or network file share services.

    OCSF Class UID: 6
    Category:

    See: https://schema.ocsf.io/1.6.0/classes/file_hosting
    """

    # Class identifiers
    class_uid: Literal[6] = Field(
        default=6, description="The unique identifier of the event class."
    )
    category_uid: Literal[0] = Field(default=0, description="The category unique identifier.")
    actor: Actor = Field(
        ..., description="The actor that performed the activity on the target file."
    )
    file: File = Field(..., description="The file that is the target of the activity.")
    metadata: Metadata = Field(
        ..., description="The metadata associated with the event or a finding."
    )
    severity_id: SeverityId = Field(
        ...,
        description="<p>The normalized identifier of the event/finding severity.</p>The normalized severity is a measurement the effort and expense required to manage and resolve an event or incident. Smaller numerical values represent lower impact events, and larger numerical values represent higher impact events.",
    )
    src_endpoint: NetworkEndpoint = Field(
        ..., description="The endpoint that performed the activity on the target file."
    )
    time: int = Field(
        ..., description="The normalized event occurrence time or the finding creation time."
    )
    type_uid: int = Field(
        ...,
        description="The event/finding type ID. It identifies the event's semantics and structure. The value is calculated by the logging system as: <code>class_uid * 100 + activity_id</code>.",
    )
    access_list: list[str] | None = Field(
        default=None, description="The list of requested access rights."
    )
    access_mask: int | None = Field(
        default=None, description="The sum of hexadecimal values of requested access rights."
    )
    access_result: dict[str, Any] | None = Field(
        default=None, description="The list of access check results."
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
    connection_info: NetworkConnectionInfo | None = Field(
        default=None, description="The network connection information."
    )
    count: int | None = Field(
        default=None,
        description="The number of times that events in the same logical group occurred during the event <strong>Start Time</strong> to <strong>End Time</strong> period.",
    )
    dst_endpoint: NetworkEndpoint | None = Field(
        default=None,
        description="The endpoint that received the activity on the target file. [Recommended]",
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
    expiration_time: int | None = Field(default=None, description="The share expiration time.")
    file_result: File | None = Field(
        default=None,
        description="The resulting file object when the activity was allowed and successful.",
    )
    http_request: HttpRequest | None = Field(
        default=None, description="Details about the underlying HTTP request. [Recommended]"
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
        default=None,
        description="The observables associated with the event or a finding. [Recommended]",
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
    share: str | None = Field(default=None, description="The share name.")
    share_type: str | None = Field(
        default=None,
        description="The share type, normalized to the caption of the share_type_id value. In the case of 'Other', it is defined by the event source.",
    )
    share_type_id: ShareTypeId | None = Field(
        default=None, description="The normalized identifier of the share type."
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
    type_name: str | None = Field(
        default=None, description="The event/finding type name, as defined by the type_uid."
    )
    unmapped: Object | None = Field(
        default=None,
        description="The attributes that are not mapped to the event schema. The names and values of those attributes are specific to the event source.",
    )
