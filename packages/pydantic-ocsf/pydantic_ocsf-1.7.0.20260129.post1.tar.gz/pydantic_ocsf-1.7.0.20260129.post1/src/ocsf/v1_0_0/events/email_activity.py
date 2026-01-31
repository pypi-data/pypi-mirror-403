"""Email Activity event class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_0_0.enums.activity_id import ActivityId
    from ocsf.v1_0_0.enums.direction_id import DirectionId
    from ocsf.v1_0_0.enums.severity_id import SeverityId
    from ocsf.v1_0_0.enums.status_id import StatusId
    from ocsf.v1_0_0.objects.email import Email
    from ocsf.v1_0_0.objects.email_auth import EmailAuth
    from ocsf.v1_0_0.objects.enrichment import Enrichment
    from ocsf.v1_0_0.objects.metadata import Metadata
    from ocsf.v1_0_0.objects.network_endpoint import NetworkEndpoint
    from ocsf.v1_0_0.objects.object import Object
    from ocsf.v1_0_0.objects.observable import Observable


class EmailActivity(OCSFBaseModel):
    """Email events report activities of emails.

    OCSF Class UID: 9
    Category: network

    See: https://schema.ocsf.io/1.0.0/classes/email_activity
    """

    # Class identifiers
    class_uid: Literal[9] = Field(
        default=9, description="The unique identifier of the event class."
    )
    category_uid: Literal[0] = Field(default=0, description="The category unique identifier.")
    direction_id: DirectionId = Field(
        ...,
        description="<p>The direction of the email relative to the scanning host or organization.</p>Email scanned at an internet gateway might be characterized as inbound to the organization from the Internet, outbound from the organization to the Internet, or internal within the organization. Email scanned at a workstation might be characterized as inbound to, or outbound from the workstation.",
    )
    email: Email = Field(..., description="The email object.")
    metadata: Metadata = Field(..., description="The metadata associated with the event.")
    severity_id: SeverityId = Field(
        ...,
        description="<p>The normalized identifier of the event severity.</p>The normalized severity is a measurement the effort and expense required to manage and resolve an event or incident. Smaller numerical values represent lower impact events, and larger numerical values represent higher impact events.",
    )
    activity_id: ActivityId | None = Field(
        default=None,
        description="The normalized identifier of the activity that triggered the event.",
    )
    attempt: int | None = Field(
        default=None, description="The attempt number for attempting to deliver the email."
    )
    banner: str | None = Field(
        default=None,
        description="The initial SMTP connection response that a messaging server receives after it connects to a email server.",
    )
    direction: str | None = Field(
        default=None,
        description="The direction of the email, as defined by the <code>direction_id</code> value.",
    )
    dst_endpoint: NetworkEndpoint | None = Field(
        default=None, description="The responder (server) receiving the email."
    )
    email_auth: EmailAuth | None = Field(
        default=None, description="The SPF, DKIM and DMARC attributes of an email. [Recommended]"
    )
    enrichments: list[Enrichment] | None = Field(
        default=None,
        description='The additional information from an external data source, which is associated with the event. For example add location information for the IP address in the DNS answers:</p><code>[{"name": "answers.ip", "value": "92.24.47.250", "type": "location", "data": {"city": "Socotra", "continent": "Asia", "coordinates": [-25.4153, 17.0743], "country": "YE", "desc": "Yemen"}}]</code>',
    )
    include: str | None = Field(default=None, description="")
    message: str | None = Field(
        default=None,
        description="The description of the event, as defined by the event source. [Recommended]",
    )
    observables: list[Observable] | None = Field(
        default=None, description="The observables associated with the event."
    )
    raw_data: str | None = Field(
        default=None, description="The event data as received from the event source."
    )
    severity: str | None = Field(
        default=None,
        description="The event severity, normalized to the caption of the severity_id value. In the case of 'Other', it is defined by the event source.",
    )
    smtp_hello: str | None = Field(
        default=None,
        description="The value of the SMTP HELO or EHLO command sent by the initiator (client). [Recommended]",
    )
    src_endpoint: NetworkEndpoint | None = Field(
        default=None, description="The initiator (client) sending the email."
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
