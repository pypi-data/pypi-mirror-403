"""Metric object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Metric(OCSFBaseModel):
    """The Metric object defines a simple name/value pair entity for a metric.

    See: https://schema.ocsf.io/1.5.0/objects/metric
    """

    name: str = Field(..., description="The name of the metric.")
    value: str = Field(..., description="The value of the metric.")
