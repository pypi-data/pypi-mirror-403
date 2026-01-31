"""Feature object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Feature(OCSFBaseModel):
    """The Feature object provides information about the software product feature that generated a specific event. It encompasses details related to the capabilities, components, user interface (UI) design, and performance upgrades associated with the feature.

    See: https://schema.ocsf.io/1.0.0/objects/feature
    """

    name: str | None = Field(default=None, description="The name of the feature.")
    uid: str | None = Field(default=None, description="The unique identifier of the feature.")
    version: str | None = Field(
        default=None, description="The version of the feature. [Recommended]"
    )
