"""Datastore Activity event class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.enums.activity_id import ActivityId
    from ocsf.v1_6_0.enums.severity_id import SeverityId
    from ocsf.v1_6_0.enums.status_id import StatusId
    from ocsf.v1_6_0.enums.type_id import TypeId
    from ocsf.v1_6_0.objects.actor import Actor
    from ocsf.v1_6_0.objects.database import Database
    from ocsf.v1_6_0.objects.databucket import Databucket
    from ocsf.v1_6_0.objects.enrichment import Enrichment
    from ocsf.v1_6_0.objects.fingerprint import Fingerprint
    from ocsf.v1_6_0.objects.http_request import HttpRequest
    from ocsf.v1_6_0.objects.http_response import HttpResponse
    from ocsf.v1_6_0.objects.metadata import Metadata
    from ocsf.v1_6_0.objects.network_endpoint import NetworkEndpoint
    from ocsf.v1_6_0.objects.object import Object
    from ocsf.v1_6_0.objects.observable import Observable
    from ocsf.v1_6_0.objects.query_info import QueryInfo
    from ocsf.v1_6_0.objects.table import Table


class DatastoreActivity(OCSFBaseModel):
    """Datastore events describe general activities (Read, Update, Query, Delete, etc.) which affect datastores or data within those datastores, e.g. (AWS RDS, AWS S3).

    OCSF Class UID: 5
    Category:

    See: https://schema.ocsf.io/1.6.0/classes/datastore_activity
    """

    # Class identifiers
    class_uid: Literal[5] = Field(
        default=5, description="The unique identifier of the event class."
    )
    category_uid: Literal[0] = Field(default=0, description="The category unique identifier.")
    actor: Actor = Field(
        ...,
        description="The actor object describes details about the user/role/process that was the source of the activity. Note that this is not the threat actor of a campaign but may be part of a campaign.",
    )
    metadata: Metadata = Field(
        ..., description="The metadata associated with the event or a finding."
    )
    severity_id: SeverityId = Field(
        ...,
        description="<p>The normalized identifier of the event/finding severity.</p>The normalized severity is a measurement the effort and expense required to manage and resolve an event or incident. Smaller numerical values represent lower impact events, and larger numerical values represent higher impact events.",
    )
    src_endpoint: NetworkEndpoint = Field(
        ..., description="Details about the source of the activity."
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
    database: Database | None = Field(
        default=None,
        description="The database object is used for databases which are typically datastore services that contain an organized collection of structured and unstructured data or a types of data. [Recommended]",
    )
    databucket: Databucket | None = Field(
        default=None,
        description="The data bucket object is a basic container that holds data, typically organized through the use of data partitions. [Recommended]",
    )
    dst_endpoint: NetworkEndpoint | None = Field(
        default=None,
        description="Details about the endpoint hosting the datastore application or service. [Recommended]",
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
    http_request: HttpRequest | None = Field(
        default=None, description="Details about the underlying http request. [Recommended]"
    )
    http_response: HttpResponse | None = Field(
        default=None, description="Details about the underlying http response. [Recommended]"
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
    query_info: QueryInfo | None = Field(
        default=None,
        description="The query info object holds information related to data access within a datastore. To access, manipulate, delete, or retrieve data from a datastore, a database query must be written using a specific syntax. [Recommended]",
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
    table: Table | None = Field(
        default=None,
        description="The table object represents a table within a structured relational database or datastore, which contains columns and rows of data that are able to be create, updated, deleted and queried. [Recommended]",
    )
    timezone_offset: int | None = Field(
        default=None,
        description="The number of minutes that the reported event <code>time</code> is ahead or behind UTC, in the range -1,080 to +1,080. [Recommended]",
    )
    type_: str | None = Field(
        default=None,
        description="The datastore resource type (e.g. database, datastore, or table).",
    )
    type_id: TypeId | None = Field(
        default=None, description="The normalized datastore resource type identifier. [Recommended]"
    )
    type_name: str | None = Field(
        default=None, description="The event/finding type name, as defined by the type_uid."
    )
    unmapped: Object | None = Field(
        default=None,
        description="The attributes that are not mapped to the event schema. The names and values of those attributes are specific to the event source.",
    )
