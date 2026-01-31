"""Discovery Details object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.objects.occurrence_details import OccurrenceDetails


class DiscoveryDetails(OCSFBaseModel):
    """The Discovery Details object describes results of a discovery task/job.

    See: https://schema.ocsf.io/1.6.0/objects/discovery_details
    """

    count: int | None = Field(
        default=None,
        description="The number of discovered entities of the specified type. [Recommended]",
    )
    occurrence_details: OccurrenceDetails | None = Field(
        default=None,
        description="Details about where in the target entity, specified information was discovered. Only the attributes, relevant to the target entity type should be populated.",
    )
    occurrences: list[OccurrenceDetails] | None = Field(
        default=None,
        description="Details about where in the target entity, specified information was discovered. Only the attributes, relevant to the target entity type should be populated.",
    )
    type_: str | None = Field(
        default=None,
        description="The specific type of information that was discovered. e.g.<code> name, phone_number, etc.</code> [Recommended]",
    )
    value: str | None = Field(
        default=None, description="Optionally, the specific value of discovered information."
    )
