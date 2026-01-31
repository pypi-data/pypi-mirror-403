"""CIS Benchmark Result object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.objects.remediation import Remediation
    from ocsf.v1_7_0.objects.rule import Rule


class CisBenchmarkResult(OCSFBaseModel):
    """The CIS Benchmark Result object contains information as defined by the Center for Internet Security (<a target='_blank' href='https://www.cisecurity.org/cis-benchmarks/'>CIS</a>) benchmark result. CIS Benchmarks are a collection of best practices for securely configuring IT systems, software, networks, and cloud infrastructure.

    See: https://schema.ocsf.io/1.7.0/objects/cis_benchmark_result
    """

    name: str = Field(..., description="The CIS benchmark name.")
    desc: str | None = Field(default=None, description="The CIS benchmark description.")
    remediation: Remediation | None = Field(
        default=None,
        description="Describes the recommended remediation steps to address identified issue(s).",
    )
    rule: Rule | None = Field(default=None, description="The CIS benchmark rule.")
