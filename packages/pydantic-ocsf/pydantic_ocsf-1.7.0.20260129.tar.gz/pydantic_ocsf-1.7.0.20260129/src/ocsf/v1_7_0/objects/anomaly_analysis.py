"""Anomaly Analysis object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.objects.analysis_target import AnalysisTarget
    from ocsf.v1_7_0.objects.anomaly import Anomaly
    from ocsf.v1_7_0.objects.baseline import Baseline


class AnomalyAnalysis(OCSFBaseModel):
    """Describes the analysis of activity patterns and anomalies of target entities to identify potential security threats, performance issues, or other deviations from established baselines. This includes monitoring and analyzing user interactions, API usage, resource utilization, access patterns and other measured indicators.

    See: https://schema.ocsf.io/1.7.0/objects/anomaly_analysis
    """

    analysis_targets: list[AnalysisTarget] = Field(
        ...,
        description="The analysis targets define the scope of monitored activities, specifying what entities, systems or processes are analyzed for activity patterns.",
    )
    anomalies: list[Anomaly] = Field(
        ...,
        description="List of detected activities that significantly deviate from the established baselines. This can include unusual access patterns, unexpected user-agents, abnormal API usage, suspicious traffic spikes, unauthorized access attempts, and other activities that may indicate potential security threats or system issues.",
    )
    baselines: list[Baseline] | None = Field(
        default=None,
        description="List of established patterns representing normal activity that serve as reference points for anomaly detection. This includes typical user interaction patterns like common user-agents, expected API access frequencies and patterns, standard resource utilization levels, and regular traffic flows. These baselines help establish what constitutes 'normal' activity in the system. [Recommended]",
    )
