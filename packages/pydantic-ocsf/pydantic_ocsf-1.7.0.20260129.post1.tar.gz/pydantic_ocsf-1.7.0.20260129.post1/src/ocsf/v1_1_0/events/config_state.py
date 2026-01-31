"""Device Config State event class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_1_0.enums.activity_id import ActivityId
    from ocsf.v1_1_0.enums.severity_id import SeverityId
    from ocsf.v1_1_0.enums.status_id import StatusId
    from ocsf.v1_1_0.objects.actor import Actor
    from ocsf.v1_1_0.objects.cis_benchmark_result import CisBenchmarkResult
    from ocsf.v1_1_0.objects.device import Device
    from ocsf.v1_1_0.objects.enrichment import Enrichment
    from ocsf.v1_1_0.objects.metadata import Metadata
    from ocsf.v1_1_0.objects.object import Object
    from ocsf.v1_1_0.objects.observable import Observable


class ConfigState(OCSFBaseModel):
    """Device Config State events report device configuration data and CIS Benchmark results.

    OCSF Class UID: 2
    Category:

    See: https://schema.ocsf.io/1.1.0/classes/config_state
    """

    # Class identifiers
    class_uid: Literal[2] = Field(
        default=2, description="The unique identifier of the event class."
    )
    category_uid: Literal[0] = Field(default=0, description="The category unique identifier.")
    device: Device = Field(
        ..., description="The device that is being discovered by an inventory process."
    )
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
    cis_benchmark_result: CisBenchmarkResult | None = Field(
        default=None, description="The CIS benchmark result. [Recommended]"
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
    raw_data: str | None = Field(
        default=None, description="The raw event/finding data as received from the source."
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
