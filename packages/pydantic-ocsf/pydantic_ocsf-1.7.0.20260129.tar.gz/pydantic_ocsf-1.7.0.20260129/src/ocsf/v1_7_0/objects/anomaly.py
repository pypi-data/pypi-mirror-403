"""Anomaly object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.objects.observation import Observation


class Anomaly(OCSFBaseModel):
    """Describes an anomaly or deviation detected in a system. Anomalies are unexpected activity patterns that could indicate potential issues needing attention.

    See: https://schema.ocsf.io/1.7.0/objects/anomaly
    """

    observation_parameter: str = Field(
        ...,
        description="The specific parameter, metric or property where the anomaly was observed. Examples include: CPU usage percentage, API response time in milliseconds, HTTP error rate, memory utilization, network latency, transaction volume, etc. This helps identify the exact aspect of the system exhibiting anomalous behavior.",
    )
    observations: list[Observation] = Field(
        ...,
        description="Details about the observed anomaly or observations that were flagged as anomalous compared to expected baseline behavior.",
    )
    observation_type: str | None = Field(
        default=None,
        description="The type of analysis methodology used to detect the anomaly. This indicates how the anomaly was identified through different analytical approaches. Common types include: Frequency Analysis, Time Pattern Analysis, Volume Analysis, Sequence Analysis, Distribution Analysis, etc. [Recommended]",
    )
    observed_pattern: str | None = Field(
        default=None,
        description="The specific pattern identified within the observation type. For Frequency Analysis, this could be 'FREQUENT', 'INFREQUENT', 'RARE', or 'UNSEEN'. For Time Pattern Analysis, this could be 'BUSINESS_HOURS', 'OFF_HOURS', or 'UNUSUAL_TIME'. For Volume Analysis, this could be 'NORMAL_VOLUME', 'HIGH_VOLUME', or 'SURGE'. The pattern values are specific to each observation type and indicate how the observed behavior relates to the baseline. [Recommended]",
    )
