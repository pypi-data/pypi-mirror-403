"""Network Connection Query event class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_2_0.enums.activity_id import ActivityId
    from ocsf.v1_2_0.enums.query_result_id import QueryResultId
    from ocsf.v1_2_0.enums.severity_id import SeverityId
    from ocsf.v1_2_0.enums.state_id import StateId
    from ocsf.v1_2_0.enums.status_id import StatusId
    from ocsf.v1_2_0.objects.enrichment import Enrichment
    from ocsf.v1_2_0.objects.metadata import Metadata
    from ocsf.v1_2_0.objects.network_connection_info import NetworkConnectionInfo
    from ocsf.v1_2_0.objects.object import Object
    from ocsf.v1_2_0.objects.observable import Observable
    from ocsf.v1_2_0.objects.process import Process
    from ocsf.v1_2_0.objects.query_info import QueryInfo


class NetworkConnectionQuery(OCSFBaseModel):
    """Network Connection Query events report information about active network connections.

    OCSF Class UID: 12
    Category:

    See: https://schema.ocsf.io/1.2.0/classes/network_connection_query
    """

    # Class identifiers
    class_uid: Literal[12] = Field(
        default=12, description="The unique identifier of the event class."
    )
    category_uid: Literal[0] = Field(default=0, description="The category unique identifier.")
    connection_info: NetworkConnectionInfo = Field(
        ..., description="The network connection information."
    )
    metadata: Metadata = Field(
        ..., description="The metadata associated with the event or a finding."
    )
    process: Process = Field(..., description="The process that owns the socket.")
    query_result_id: QueryResultId = Field(
        ..., description="The normalized identifier of the query result."
    )
    severity_id: SeverityId = Field(
        ...,
        description="<p>The normalized identifier of the event/finding severity.</p>The normalized severity is a measurement the effort and expense required to manage and resolve an event or incident. Smaller numerical values represent lower impact events, and larger numerical values represent higher impact events.",
    )
    state_id: StateId = Field(..., description="The state of the socket.")
    activity_id: ActivityId | None = Field(
        default=None,
        description="The normalized identifier of the activity that triggered the event.",
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
    query_info: QueryInfo | None = Field(
        default=None,
        description="The search details associated with the query request. [Recommended]",
    )
    query_result: str | None = Field(
        default=None, description="The result of the query. [Recommended]"
    )
    raw_data: str | None = Field(
        default=None, description="The raw event/finding data as received from the source."
    )
    severity: str | None = Field(
        default=None,
        description="The event/finding severity, normalized to the caption of the severity_id value. In the case of 'Other', it is defined by the source.",
    )
    state: str | None = Field(
        default=None,
        description="The state of the socket, normalized to the caption of the state_id value. In the case of 'Other', it is defined by the event source. [Recommended]",
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
    unmapped: Object | None = Field(
        default=None,
        description="The attributes that are not mapped to the event schema. The names and values of those attributes are specific to the event source.",
    )
