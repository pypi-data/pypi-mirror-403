"""SMB Activity event class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_0_0.enums.activity_id import ActivityId
    from ocsf.v1_0_0.enums.severity_id import SeverityId
    from ocsf.v1_0_0.enums.share_type_id import ShareTypeId
    from ocsf.v1_0_0.enums.status_id import StatusId
    from ocsf.v1_0_0.objects.dce_rpc import DceRpc
    from ocsf.v1_0_0.objects.enrichment import Enrichment
    from ocsf.v1_0_0.objects.file import File
    from ocsf.v1_0_0.objects.metadata import Metadata
    from ocsf.v1_0_0.objects.object import Object
    from ocsf.v1_0_0.objects.observable import Observable
    from ocsf.v1_0_0.objects.response import Response


class SmbActivity(OCSFBaseModel):
    """Server Message Block (SMB) Protocol Activity events report client/server connections sharing resources within the network.

    OCSF Class UID: 6
    Category:

    See: https://schema.ocsf.io/1.0.0/classes/smb_activity
    """

    # Class identifiers
    class_uid: Literal[6] = Field(
        default=6, description="The unique identifier of the event class."
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
    client_dialects: list[str] | None = Field(
        default=None, description="The list of SMB dialects that the client speaks. [Recommended]"
    )
    command: str | None = Field(
        default=None,
        description="The command name (e.g. SMB2_COMMAND_CREATE, SMB1_COMMAND_WRITE_ANDX). [Recommended]",
    )
    dce_rpc: DceRpc | None = Field(
        default=None,
        description="The DCE/RPC object describes the remote procedure call system for distributed computing environments.",
    )
    dialect: str | None = Field(
        default=None, description="The negotiated protocol dialect. [Recommended]"
    )
    enrichments: list[Enrichment] | None = Field(
        default=None,
        description='The additional information from an external data source, which is associated with the event. For example add location information for the IP address in the DNS answers:</p><code>[{"name": "answers.ip", "value": "92.24.47.250", "type": "location", "data": {"city": "Socotra", "continent": "Asia", "coordinates": [-25.4153, 17.0743], "country": "YE", "desc": "Yemen"}}]</code>',
    )
    file: File | None = Field(
        default=None, description="The file that is the target of the SMB activity. [Recommended]"
    )
    include: str | None = Field(default=None, description="")
    message: str | None = Field(
        default=None,
        description="The description of the event, as defined by the event source. [Recommended]",
    )
    observables: list[Observable] | None = Field(
        default=None, description="The observables associated with the event."
    )
    open_type: str | None = Field(
        default=None,
        description="Indicates how the file was opened (e.g. normal, delete on close). [Recommended]",
    )
    raw_data: str | None = Field(
        default=None, description="The event data as received from the event source."
    )
    response: Response | None = Field(
        default=None, description="The server response in an SMB network connection. [Recommended]"
    )
    severity: str | None = Field(
        default=None,
        description="The event severity, normalized to the caption of the severity_id value. In the case of 'Other', it is defined by the event source.",
    )
    share: str | None = Field(default=None, description="The SMB share name.")
    share_type: str | None = Field(
        default=None,
        description="The SMB share type, normalized to the caption of the share_type_id value. In the case of 'Other', it is defined by the event source.",
    )
    share_type_id: ShareTypeId | None = Field(
        default=None, description="The normalized identifier of the SMB share type. [Recommended]"
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
    tree_uid: str | None = Field(
        default=None,
        description="The tree id is a unique SMB identifier which represents an open connection to a share.",
    )
    unmapped: Object | None = Field(
        default=None,
        description="The attributes that are not mapped to the event schema. The names and values of those attributes are specific to the event source.",
    )
