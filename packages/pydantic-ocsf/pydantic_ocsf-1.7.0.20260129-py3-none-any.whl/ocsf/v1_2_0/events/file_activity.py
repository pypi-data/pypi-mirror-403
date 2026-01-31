"""File System Activity event class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_2_0.enums.activity_id import ActivityId
    from ocsf.v1_2_0.enums.severity_id import SeverityId
    from ocsf.v1_2_0.enums.status_id import StatusId
    from ocsf.v1_2_0.objects.actor import Actor
    from ocsf.v1_2_0.objects.device import Device
    from ocsf.v1_2_0.objects.enrichment import Enrichment
    from ocsf.v1_2_0.objects.file import File
    from ocsf.v1_2_0.objects.metadata import Metadata
    from ocsf.v1_2_0.objects.object import Object
    from ocsf.v1_2_0.objects.observable import Observable


class FileActivity(OCSFBaseModel):
    """File System Activity events report when a process performs an action on a file or folder.

    OCSF Class UID: 1
    Category:

    See: https://schema.ocsf.io/1.2.0/classes/file_activity
    """

    # Class identifiers
    class_uid: Literal[1] = Field(
        default=1, description="The unique identifier of the event class."
    )
    category_uid: Literal[0] = Field(default=0, description="The category unique identifier.")
    actor: Actor = Field(
        ..., description="The actor that performed the activity on the <code>file</code> object"
    )
    device: Device = Field(..., description="An addressable device, computer system or host.")
    file: File = Field(..., description="The file that is the target of the activity.")
    metadata: Metadata = Field(
        ..., description="The metadata associated with the event or a finding."
    )
    severity_id: SeverityId = Field(
        ...,
        description="<p>The normalized identifier of the event/finding severity.</p>The normalized severity is a measurement the effort and expense required to manage and resolve an event or incident. Smaller numerical values represent lower impact events, and larger numerical values represent higher impact events.",
    )
    access_mask: int | None = Field(
        default=None, description="The access mask in a platform-native format."
    )
    activity_id: ActivityId | None = Field(
        default=None,
        description="The normalized identifier of the activity that triggered the event.",
    )
    component: str | None = Field(
        default=None,
        description="<p>The name or relative pathname of a sub-component of the data object, if applicable. </p>For example: <code>attachment.doc</code>, <code>attachment.zip/bad.doc</code>, or <code>part.mime/part.cab/part.uue/part.doc</code>. [Recommended]",
    )
    connection_uid: str | None = Field(
        default=None, description="The network connection identifier."
    )
    create_mask: str | None = Field(
        default=None,
        description="The original Windows mask that is required to create the object. [Recommended]",
    )
    enrichments: list[Enrichment] | None = Field(
        default=None,
        description='The additional information from an external data source, which is associated with the event or a finding. For example add location information for the IP address in the DNS answers:</p><code>[{"name": "answers.ip", "value": "92.24.47.250", "type": "location", "data": {"city": "Socotra", "continent": "Asia", "coordinates": [-25.4153, 17.0743], "country": "YE", "desc": "Yemen"}}]</code>',
    )
    file_diff: str | None = Field(
        default=None,
        description="File content differences used for change detection. For example, a common use case is to identify itemized changes within INI or configuration/property setting values. [Recommended]",
    )
    file_result: File | None = Field(
        default=None,
        description="The resulting file object when the activity was allowed and successful. [Recommended]",
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
    unmapped: Object | None = Field(
        default=None,
        description="The attributes that are not mapped to the event schema. The names and values of those attributes are specific to the event source.",
    )
