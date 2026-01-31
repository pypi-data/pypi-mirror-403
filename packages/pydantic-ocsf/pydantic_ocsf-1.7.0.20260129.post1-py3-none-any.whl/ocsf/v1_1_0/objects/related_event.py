"""Related Event object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_1_0.objects.attack import Attack
    from ocsf.v1_1_0.objects.kill_chain_phase import KillChainPhase
    from ocsf.v1_1_0.objects.observable import Observable


class RelatedEvent(OCSFBaseModel):
    """The Related Event object describes an event related to a finding or detection as identified by the security product.

    See: https://schema.ocsf.io/1.1.0/objects/related_event
    """

    uid: str = Field(..., description="The unique identifier of the related event.")
    attacks: list[Attack] | None = Field(
        default=None,
        description="An array of <a target='_blank' href='https://attack.mitre.org'>MITRE ATT&CK®</a> objects describing the tactics, techniques & sub-techniques identified by a security control or finding.",
    )
    kill_chain: list[KillChainPhase] | None = Field(
        default=None,
        description="The <a target='_blank' href='https://www.lockheedmartin.com/en-us/capabilities/cyber/cyber-kill-chain.html'>Cyber Kill Chain®</a> provides a detailed description of each phase and its associated activities within the broader context of a cyber attack.",
    )
    observables: list[Observable] | None = Field(
        default=None, description="The observables associated with the event or a finding."
    )
    product_uid: str | None = Field(
        default=None,
        description="The unique identifier of the product that reported the related event.",
    )
    type_: str | None = Field(
        default=None,
        description="The type of the related event. For example: Process Activity: Launch.",
    )
    type_uid: int | None = Field(
        default=None,
        description="The unique identifier of the related event type. For example: 100701. [Recommended]",
    )
