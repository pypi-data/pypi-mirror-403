"""Process Activity event class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_0_0.enums.activity_id import ActivityId
    from ocsf.v1_0_0.enums.injection_type_id import InjectionTypeId
    from ocsf.v1_0_0.enums.severity_id import SeverityId
    from ocsf.v1_0_0.enums.status_id import StatusId
    from ocsf.v1_0_0.objects.actor import Actor
    from ocsf.v1_0_0.objects.device import Device
    from ocsf.v1_0_0.objects.enrichment import Enrichment
    from ocsf.v1_0_0.objects.metadata import Metadata
    from ocsf.v1_0_0.objects.module import Module
    from ocsf.v1_0_0.objects.object import Object
    from ocsf.v1_0_0.objects.observable import Observable
    from ocsf.v1_0_0.objects.process import Process


class ProcessActivity(OCSFBaseModel):
    """Process Activity events report when a process launches, injects, opens or terminates another process, successful or otherwise.

    OCSF Class UID: 7
    Category:

    See: https://schema.ocsf.io/1.0.0/classes/process_activity
    """

    # Class identifiers
    class_uid: Literal[7] = Field(
        default=7, description="The unique identifier of the event class."
    )
    category_uid: Literal[0] = Field(default=0, description="The category unique identifier.")
    device: Device = Field(..., description="An addressable device, computer system or host.")
    metadata: Metadata = Field(..., description="The metadata associated with the event.")
    process: Process = Field(
        ..., description="The process that was launched, injected into, opened, or terminated."
    )
    severity_id: SeverityId = Field(
        ...,
        description="<p>The normalized identifier of the event severity.</p>The normalized severity is a measurement the effort and expense required to manage and resolve an event or incident. Smaller numerical values represent lower impact events, and larger numerical values represent higher impact events.",
    )
    activity_id: ActivityId | None = Field(
        default=None,
        description="The normalized identifier of the activity that triggered the event.",
    )
    actor: Actor | None = Field(
        default=None,
        description="The actor that performed the activity on the target <code>process</code>. For example, the process that started a new process or injected code into another process.",
    )
    actual_permissions: int | None = Field(
        default=None,
        description="The permissions that were granted to the in a platform-native format.",
    )
    enrichments: list[Enrichment] | None = Field(
        default=None,
        description='The additional information from an external data source, which is associated with the event. For example add location information for the IP address in the DNS answers:</p><code>[{"name": "answers.ip", "value": "92.24.47.250", "type": "location", "data": {"city": "Socotra", "continent": "Asia", "coordinates": [-25.4153, 17.0743], "country": "YE", "desc": "Yemen"}}]</code>',
    )
    exit_code: int | None = Field(
        default=None,
        description="The exit code reported by a process when it terminates. The convention is that zero indicates success and any non-zero exit code indicates that some error occurred.",
    )
    include: str | None = Field(default=None, description="")
    injection_type: str | None = Field(
        default=None,
        description="The process injection method, normalized to the caption of the injection_type_id value. In the case of 'Other', it is defined by the event source.",
    )
    injection_type_id: InjectionTypeId | None = Field(
        default=None, description="The normalized identifier of the process injection method."
    )
    message: str | None = Field(
        default=None,
        description="The description of the event, as defined by the event source. [Recommended]",
    )
    module: Module | None = Field(
        default=None, description="The module that was injected by the actor process."
    )
    observables: list[Observable] | None = Field(
        default=None, description="The observables associated with the event."
    )
    raw_data: str | None = Field(
        default=None, description="The event data as received from the event source."
    )
    requested_permissions: int | None = Field(
        default=None, description="The permissions mask that were requested by the process."
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
