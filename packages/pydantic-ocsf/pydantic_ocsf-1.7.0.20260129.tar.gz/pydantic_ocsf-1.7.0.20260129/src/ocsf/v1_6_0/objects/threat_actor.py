"""Threat Actor object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.enums.type_id import TypeId


class ThreatActor(OCSFBaseModel):
    """Threat actor is responsible for the observed malicious activity.

    See: https://schema.ocsf.io/1.6.0/objects/threat_actor
    """

    name: str = Field(..., description="The name of the threat actor.")
    type_: str | None = Field(
        default=None,
        description="The classification of the threat actor based on their motivations, capabilities, or affiliations. Common types include nation-state actors, cybercriminal groups, hacktivists, or insider threats.",
    )
    type_id: TypeId | None = Field(
        default=None, description="The normalized datastore resource type identifier. [Recommended]"
    )
