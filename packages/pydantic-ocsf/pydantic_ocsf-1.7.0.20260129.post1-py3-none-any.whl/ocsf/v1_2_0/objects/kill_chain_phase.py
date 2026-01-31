"""Kill Chain Phase object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_2_0.enums.phase_id import PhaseId


class KillChainPhase(OCSFBaseModel):
    """The Kill Chain Phase object represents a single phase of a cyber attack, including the initial reconnaissance and planning stages up to the final objective of the attacker. It provides a detailed description of each phase and its associated activities within the broader context of a cyber attack. See <a target='_blank' href='https://www.lockheedmartin.com/en-us/capabilities/cyber/cyber-kill-chain.html'>Cyber Kill Chain®</a>.

    See: https://schema.ocsf.io/1.2.0/objects/kill_chain_phase
    """

    phase_id: PhaseId = Field(..., description="The cyber kill chain phase identifier.")
    phase: str | None = Field(default=None, description="The cyber kill chain phase. [Recommended]")
