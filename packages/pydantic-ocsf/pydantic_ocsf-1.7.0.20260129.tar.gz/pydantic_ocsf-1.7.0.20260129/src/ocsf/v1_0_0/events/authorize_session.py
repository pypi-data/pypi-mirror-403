"""Authorize Session event class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_0_0.enums.activity_id import ActivityId
    from ocsf.v1_0_0.enums.severity_id import SeverityId
    from ocsf.v1_0_0.enums.status_id import StatusId
    from ocsf.v1_0_0.objects.enrichment import Enrichment
    from ocsf.v1_0_0.objects.group import Group
    from ocsf.v1_0_0.objects.metadata import Metadata
    from ocsf.v1_0_0.objects.network_endpoint import NetworkEndpoint
    from ocsf.v1_0_0.objects.object import Object
    from ocsf.v1_0_0.objects.observable import Observable
    from ocsf.v1_0_0.objects.session import Session
    from ocsf.v1_0_0.objects.user import User


class AuthorizeSession(OCSFBaseModel):
    """Authorize Session events report privileges or groups assigned to a new user session, usually at login time.

    OCSF Class UID: 3
    Category:

    See: https://schema.ocsf.io/1.0.0/classes/authorize_session
    """

    # Class identifiers
    class_uid: Literal[3] = Field(
        default=3, description="The unique identifier of the event class."
    )
    category_uid: Literal[0] = Field(default=0, description="The category unique identifier.")
    metadata: Metadata = Field(..., description="The metadata associated with the event.")
    severity_id: SeverityId = Field(
        ...,
        description="<p>The normalized identifier of the event severity.</p>The normalized severity is a measurement the effort and expense required to manage and resolve an event or incident. Smaller numerical values represent lower impact events, and larger numerical values represent higher impact events.",
    )
    user: User = Field(..., description="The user to which new privileges were assigned.")
    activity_id: ActivityId | None = Field(
        default=None,
        description="The normalized identifier of the activity that triggered the event.",
    )
    dst_endpoint: NetworkEndpoint | None = Field(
        default=None, description="The Endpoint for which the user session was targeted."
    )
    enrichments: list[Enrichment] | None = Field(
        default=None,
        description='The additional information from an external data source, which is associated with the event. For example add location information for the IP address in the DNS answers:</p><code>[{"name": "answers.ip", "value": "92.24.47.250", "type": "location", "data": {"city": "Socotra", "continent": "Asia", "coordinates": [-25.4153, 17.0743], "country": "YE", "desc": "Yemen"}}]</code>',
    )
    group: Group | None = Field(
        default=None, description="Group that was assigned to the new user session. [Recommended]"
    )
    include: str | None = Field(default=None, description="")
    message: str | None = Field(
        default=None,
        description="The description of the event, as defined by the event source. [Recommended]",
    )
    observables: list[Observable] | None = Field(
        default=None, description="The observables associated with the event."
    )
    privileges: list[str] | None = Field(
        default=None,
        description="The list of sensitive privileges, assigned to the new user session. [Recommended]",
    )
    raw_data: str | None = Field(
        default=None, description="The event data as received from the event source."
    )
    session: Session | None = Field(
        default=None, description="The user session with the assigned privileges. [Recommended]"
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
