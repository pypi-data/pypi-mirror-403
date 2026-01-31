"""Reporter object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.objects.organization import Organization


class Reporter(OCSFBaseModel):
    """The entity from which an event or finding was reported.

    See: https://schema.ocsf.io/1.7.0/objects/reporter
    """

    hostname: Any | None = Field(
        default=None,
        description="The hostname of the entity from which the event or finding was reported. [Recommended]",
    )
    ip: Any | None = Field(
        default=None,
        description="The IP address of the entity from which the event or finding was reported. [Recommended]",
    )
    name: str | None = Field(
        default=None,
        description="The name of the entity from which the event or finding was reported. [Recommended]",
    )
    org: Organization | None = Field(
        default=None,
        description="The organization properties of the entity that reported the event or finding.",
    )
    uid: str | None = Field(
        default=None,
        description="The unique identifier of the entity from which the event or finding was reported. [Recommended]",
    )
