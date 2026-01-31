"""Device Config State Change event class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_1_0.enums.activity_id import ActivityId
    from ocsf.v1_1_0.enums.prev_security_level_id import PrevSecurityLevelId
    from ocsf.v1_1_0.enums.security_level_id import SecurityLevelId
    from ocsf.v1_1_0.enums.severity_id import SeverityId
    from ocsf.v1_1_0.enums.status_id import StatusId
    from ocsf.v1_1_0.objects.actor import Actor
    from ocsf.v1_1_0.objects.device import Device
    from ocsf.v1_1_0.objects.enrichment import Enrichment
    from ocsf.v1_1_0.objects.metadata import Metadata
    from ocsf.v1_1_0.objects.object import Object
    from ocsf.v1_1_0.objects.observable import Observable
    from ocsf.v1_1_0.objects.security_state import SecurityState


class DeviceConfigStateChange(OCSFBaseModel):
    """Device Config State Change events report state changes that impact the security of the device.

    OCSF Class UID: 19
    Category:

    See: https://schema.ocsf.io/1.1.0/classes/device_config_state_change
    """

    # Class identifiers
    class_uid: Literal[19] = Field(
        default=19, description="The unique identifier of the event class."
    )
    category_uid: Literal[0] = Field(default=0, description="The category unique identifier.")
    device: Device = Field(..., description="The device that is impacted by the state change.")
    metadata: Metadata = Field(
        ..., description="The metadata associated with the event or a finding."
    )
    severity_id: SeverityId = Field(
        ...,
        description="<p>The normalized identifier of the event/finding severity.</p>The normalized severity is a measurement the effort and expense required to manage and resolve an event or incident. Smaller numerical values represent lower impact events, and larger numerical values represent higher impact events.",
    )
    activity_id: ActivityId | None = Field(
        default=None,
        description="The normalized identifier of the activity that triggered the event.",
    )
    actor: Actor | None = Field(
        default=None,
        description="The actor object describes details about the user/role/process that was the source of the activity.",
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
        default=None, description="The observables associated with the event or a finding."
    )
    prev_security_level: str | None = Field(
        default=None, description="The previous security level of the entity"
    )
    prev_security_level_id: PrevSecurityLevelId | None = Field(
        default=None, description="The previous security level of the entity"
    )
    prev_security_states: list[SecurityState] | None = Field(
        default=None, description="The previous security states of the device."
    )
    raw_data: str | None = Field(
        default=None, description="The raw event/finding data as received from the source."
    )
    security_level: str | None = Field(
        default=None, description="The current security level of the entity"
    )
    security_level_id: SecurityLevelId | None = Field(
        default=None, description="The current security level of the entity"
    )
    security_states: list[SecurityState] | None = Field(
        default=None, description="The current security states of the device."
    )
    severity: str | None = Field(
        default=None,
        description="The event/finding severity, normalized to the caption of the severity_id value. In the case of 'Other', it is defined by the source.",
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
    unmapped: Object | None = Field(
        default=None,
        description="The attributes that are not mapped to the event schema. The names and values of those attributes are specific to the event source.",
    )
