"""Related Event/Finding object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.enums.severity_id import SeverityId
    from ocsf.v1_6_0.objects.attack import Attack
    from ocsf.v1_6_0.objects.key_value_object import KeyValueObject
    from ocsf.v1_6_0.objects.kill_chain_phase import KillChainPhase
    from ocsf.v1_6_0.objects.observable import Observable
    from ocsf.v1_6_0.objects.product import Product
    from ocsf.v1_6_0.objects.trait import Trait


class RelatedEvent(OCSFBaseModel):
    """The Related Event object describes an event or another finding related to a finding. It may or may not be an OCSF event.

    See: https://schema.ocsf.io/1.6.0/objects/related_event
    """

    uid: str = Field(
        ...,
        description="The unique identifier of the related event/finding.</p> If the related event/finding is in OCSF, then this value must be equal to <code>metadata.uid</code> in the corresponding event.",
    )
    attacks: list[Attack] | None = Field(
        default=None,
        description="An array of MITRE ATT&CK® objects describing identified tactics, techniques & sub-techniques. The objects are compatible with MITRE ATLAS™ tactics, techniques & sub-techniques.",
    )
    count: int | None = Field(
        default=None,
        description="The number of times that activity in the same logical group occurred, as reported by the related Finding.",
    )
    created_time: int | None = Field(
        default=None, description="The time when the related event/finding was created."
    )
    desc: str | None = Field(
        default=None, description="A description of the related event/finding."
    )
    first_seen_time: int | None = Field(
        default=None,
        description="The time when the finding was first observed. e.g. The time when a vulnerability was first observed.<br>It can differ from the <code>created_time</code> timestamp, which reflects the time this finding was created.",
    )
    kill_chain: list[KillChainPhase] | None = Field(
        default=None,
        description="The <a target='_blank' href='https://www.lockheedmartin.com/en-us/capabilities/cyber/cyber-kill-chain.html'>Cyber Kill Chain®</a> provides a detailed description of each phase and its associated activities within the broader context of a cyber attack.",
    )
    last_seen_time: int | None = Field(
        default=None,
        description="The time when the finding was most recently observed. e.g. The time when a vulnerability was most recently observed.<br>It can differ from the <code>modified_time</code> timestamp, which reflects the time this finding was last modified.",
    )
    modified_time: int | None = Field(
        default=None, description="The time when the related event/finding was last modified."
    )
    observables: list[Observable] | None = Field(
        default=None, description="The observables associated with the event or a finding."
    )
    product: Product | None = Field(
        default=None,
        description="Details about the product that reported the related event/finding.",
    )
    product_uid: str | None = Field(
        default=None,
        description="The unique identifier of the product that reported the related event.",
    )
    severity: str | None = Field(
        default=None,
        description="The event/finding severity, normalized to the caption of the <code>severity_id</code> value. In the case of 'Other', it is defined by the source.",
    )
    severity_id: SeverityId | None = Field(
        default=None,
        description="<p>The normalized identifier of the event/finding severity.</p>The normalized severity is a measurement the effort and expense required to manage and resolve an event or incident. Smaller numerical values represent lower impact events, and larger numerical values represent higher impact events. [Recommended]",
    )
    status: str | None = Field(
        default=None,
        description="The related event status. Should correspond to the label of the status_id (or 'Other' status value for status_id = 99) of the related event.",
    )
    tags: list[KeyValueObject] | None = Field(
        default=None,
        description="The list of tags; <code>{key:value}</code> pairs associated with the related event/finding.",
    )
    title: str | None = Field(
        default=None, description="A title or a brief phrase summarizing the related event/finding."
    )
    traits: list[Trait] | None = Field(
        default=None,
        description="The list of key traits or characteristics extracted from the related event/finding that influenced or contributed to the overall finding's outcome.",
    )
    type_: str | None = Field(
        default=None,
        description="The type of the related event/finding.</p>Populate if the related event/finding is <code>NOT</code> in OCSF. If it is in OCSF, then utilize <code>type_name, type_uid</code> instead.",
    )
    type_name: str | None = Field(
        default=None,
        description="The type of the related OCSF event, as defined by <code>type_uid</code>.<p>For example: <code>Process Activity: Launch.</code></p>Populate if the related event/finding is in OCSF.",
    )
    type_uid: int | None = Field(
        default=None,
        description="The unique identifier of the related OCSF event type. <p>For example: <code>100701.</code></p>Populate if the related event/finding is in OCSF. [Recommended]",
    )
