"""Autonomous System object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class AutonomousSystem(OCSFBaseModel):
    """An autonomous system (AS) is a collection of connected Internet Protocol (IP) routing prefixes under the control of one or more network operators on behalf of a single administrative entity or domain that presents a common, clearly defined routing policy to the internet.

    See: https://schema.ocsf.io/1.7.0/objects/autonomous_system
    """

    name: str | None = Field(
        default=None, description="Organization name for the Autonomous System. [Recommended]"
    )
    number: int | None = Field(
        default=None, description="Unique number that the AS is identified by. [Recommended]"
    )
