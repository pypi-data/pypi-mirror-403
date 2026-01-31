"""Observation object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.objects.timespan import Timespan


class Observation(OCSFBaseModel):
    """A record of an observed value or event that captures the timing and frequency of its occurrence. Used to track when values/events were first detected, last detected, and their total occurrence count.

    See: https://schema.ocsf.io/1.7.0/objects/observation
    """

    value: str = Field(
        ...,
        description="The specific value, event, indicator or data point that was observed and recorded. This is the core piece of information being tracked.",
    )
    count: int | None = Field(
        default=None,
        description="Integer representing the total number of times this specific value/event was observed across all occurrences. Helps establish prevalence and patterns. [Recommended]",
    )
    timespan: Timespan | None = Field(
        default=None,
        description="The time window when the value or event was first observed. It is used to analyze activity patterns, detect trends, or correlate events within a specific timeframe. [Recommended]",
    )
