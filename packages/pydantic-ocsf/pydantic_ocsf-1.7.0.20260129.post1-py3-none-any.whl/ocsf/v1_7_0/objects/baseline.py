"""Baseline object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.objects.observation import Observation


class Baseline(OCSFBaseModel):
    """Describes the baseline or expected behavior of a system, service, or component based on historical observations and measurements. It establishes reference points for comparison to detect anomalies, trends, and deviations from typical patterns.

    See: https://schema.ocsf.io/1.7.0/objects/baseline
    """

    observation_parameter: str = Field(
        ...,
        description="The specific parameter or property being monitored. Examples include: CPU usage percentage, API response time in milliseconds, HTTP error rate, memory utilization, network latency, transaction volume, etc.",
    )
    observations: list[Observation] = Field(
        ...,
        description="Collection of actual measured values, data points and observations recorded for this baseline.",
    )
    observation_type: str | None = Field(
        default=None,
        description="The type of analysis being performed to establish baseline behavior. Common types include: Frequency Analysis, Time Pattern Analysis, Volume Analysis, Sequence Analysis, Distribution Analysis, etc. [Recommended]",
    )
    observed_pattern: str | None = Field(
        default=None,
        description="The specific pattern identified within the observation type. For Frequency Analysis, this could be 'FREQUENT', 'INFREQUENT', 'RARE', or 'UNSEEN'. For Time Pattern Analysis, this could be 'BUSINESS_HOURS', 'OFF_HOURS', or 'UNUSUAL_TIME'. For Volume Analysis, this could be 'NORMAL_VOLUME', 'HIGH_VOLUME', or 'SURGE'. The pattern values are specific to each observation type and indicate the baseline behavior. [Recommended]",
    )
