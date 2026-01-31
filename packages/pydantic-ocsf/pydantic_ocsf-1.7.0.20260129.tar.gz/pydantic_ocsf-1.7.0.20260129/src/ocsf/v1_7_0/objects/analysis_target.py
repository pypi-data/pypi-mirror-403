"""Analysis Target object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class AnalysisTarget(OCSFBaseModel):
    """The analysis target defines the scope of monitored activities, specifying what entity, system or process is analyzed for activity patterns.

    See: https://schema.ocsf.io/1.7.0/objects/analysis_target
    """

    name: str = Field(
        ...,
        description="The specific name or identifier of the analysis target, such as the username of a User Account, the name of a Kubernetes Cluster, the identifier of a Network Namespace, or the name of an Application Component.",
    )
    type_: str | None = Field(
        default=None,
        description="The category of the analysis target, such as User Account, Kubernetes Cluster, Network Namespace, or Application Component.",
    )
