"""Authentication event class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_1_0.enums.activity_id import ActivityId
    from ocsf.v1_1_0.enums.auth_protocol_id import AuthProtocolId
    from ocsf.v1_1_0.enums.logon_type_id import LogonTypeId
    from ocsf.v1_1_0.enums.severity_id import SeverityId
    from ocsf.v1_1_0.enums.status_id import StatusId
    from ocsf.v1_1_0.objects.actor import Actor
    from ocsf.v1_1_0.objects.certificate import Certificate
    from ocsf.v1_1_0.objects.enrichment import Enrichment
    from ocsf.v1_1_0.objects.http_request import HttpRequest
    from ocsf.v1_1_0.objects.metadata import Metadata
    from ocsf.v1_1_0.objects.network_endpoint import NetworkEndpoint
    from ocsf.v1_1_0.objects.object import Object
    from ocsf.v1_1_0.objects.observable import Observable
    from ocsf.v1_1_0.objects.process import Process
    from ocsf.v1_1_0.objects.service import Service
    from ocsf.v1_1_0.objects.session import Session
    from ocsf.v1_1_0.objects.user import User


class Authentication(OCSFBaseModel):
    """Authentication events report authentication session activities such as user attempts a logon or logoff, successfully or otherwise.

    OCSF Class UID: 2
    Category:

    See: https://schema.ocsf.io/1.1.0/classes/authentication
    """

    # Class identifiers
    class_uid: Literal[2] = Field(
        default=2, description="The unique identifier of the event class."
    )
    category_uid: Literal[0] = Field(default=0, description="The category unique identifier.")
    metadata: Metadata = Field(
        ..., description="The metadata associated with the event or a finding."
    )
    severity_id: SeverityId = Field(
        ...,
        description="<p>The normalized identifier of the event/finding severity.</p>The normalized severity is a measurement the effort and expense required to manage and resolve an event or incident. Smaller numerical values represent lower impact events, and larger numerical values represent higher impact events.",
    )
    user: User = Field(..., description="The subject (user/role or account) to authenticate.")
    activity_id: ActivityId | None = Field(
        default=None,
        description="The normalized identifier of the activity that triggered the event.",
    )
    actor: Actor | None = Field(
        default=None, description="The actor that requested the authentication."
    )
    auth_protocol: str | None = Field(
        default=None,
        description="The authentication protocol as defined by the caption of 'auth_protocol_id'. In the case of 'Other', it is defined by the event source.",
    )
    auth_protocol_id: AuthProtocolId | None = Field(
        default=None,
        description="The normalized identifier of the authentication protocol used to create the user session. [Recommended]",
    )
    certificate: Certificate | None = Field(
        default=None,
        description="The certificate associated with the authentication or pre-authentication (Kerberos).",
    )
    dst_endpoint: NetworkEndpoint | None = Field(
        default=None,
        description="The endpoint to which the authentication was targeted. [Recommended]",
    )
    enrichments: list[Enrichment] | None = Field(
        default=None,
        description='The additional information from an external data source, which is associated with the event or a finding. For example add location information for the IP address in the DNS answers:</p><code>[{"name": "answers.ip", "value": "92.24.47.250", "type": "location", "data": {"city": "Socotra", "continent": "Asia", "coordinates": [-25.4153, 17.0743], "country": "YE", "desc": "Yemen"}}]</code>',
    )
    http_request: HttpRequest | None = Field(
        default=None, description="Details about the underlying http request."
    )
    include: str | None = Field(default=None, description="")
    is_cleartext: bool | None = Field(
        default=None,
        description="Indicates whether the credentials were passed in clear text.<p><b>Note:</b> True if the credentials were passed in a clear text protocol such as FTP or TELNET, or if Windows detected that a user's logon password was passed to the authentication package in clear text.</p>",
    )
    is_mfa: bool | None = Field(
        default=None,
        description="Indicates whether Multi Factor Authentication was used during authentication.",
    )
    is_new_logon: bool | None = Field(
        default=None,
        description="Indicates logon is from a device not seen before or a first time account logon.",
    )
    is_remote: bool | None = Field(
        default=None,
        description="The attempted authentication is over a remote connection. [Recommended]",
    )
    logon_process: Process | None = Field(
        default=None,
        description="The trusted process that validated the authentication credentials.",
    )
    logon_type: str | None = Field(
        default=None,
        description="The logon type, normalized to the caption of the logon_type_id value. In the case of 'Other', it is defined by the event source.",
    )
    logon_type_id: LogonTypeId | None = Field(
        default=None, description="The normalized logon type identifier. [Recommended]"
    )
    message: str | None = Field(
        default=None,
        description="The description of the event/finding, as defined by the source. [Recommended]",
    )
    observables: list[Observable] | None = Field(
        default=None, description="The observables associated with the event or a finding."
    )
    raw_data: str | None = Field(
        default=None, description="The raw event/finding data as received from the source."
    )
    service: Service | None = Field(
        default=None,
        description="The service or gateway to which the user or process is being authenticated [Recommended]",
    )
    session: Session | None = Field(
        default=None, description="The authenticated user or service session."
    )
    severity: str | None = Field(
        default=None,
        description="The event/finding severity, normalized to the caption of the severity_id value. In the case of 'Other', it is defined by the source.",
    )
    src_endpoint: NetworkEndpoint | None = Field(
        default=None, description="The Endpoint from which the authentication was requested."
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
        description="The details about the authentication request. For example, possible details for Windows logon or logoff events are:<ul><li>Success</li><ul><li>LOGOFF_USER_INITIATED</li><li>LOGOFF_OTHER</li></ul><li>Failure</li><ul><li>USER_DOES_NOT_EXIST</li><li>INVALID_CREDENTIALS</li><li>ACCOUNT_DISABLED</li><li>ACCOUNT_LOCKED_OUT</li><li>PASSWORD_EXPIRED</li></ul></ul>",
    )
    status_id: StatusId | None = Field(
        default=None, description="The normalized identifier of the event status. [Recommended]"
    )
    unmapped: Object | None = Field(
        default=None,
        description="The attributes that are not mapped to the event schema. The names and values of those attributes are specific to the event source.",
    )
