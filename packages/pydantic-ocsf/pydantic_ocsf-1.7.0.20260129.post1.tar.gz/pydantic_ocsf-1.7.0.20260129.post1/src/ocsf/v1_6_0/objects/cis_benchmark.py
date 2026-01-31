"""CIS Benchmark object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.objects.cis_control import CisControl


class CisBenchmark(OCSFBaseModel):
    """The CIS Benchmark object describes best practices for securely configuring IT systems, software, networks, and cloud infrastructure as defined by the <a target='_blank' href='https://www.cisecurity.org/cis-benchmarks/'>Center for Internet Security</a>. See also <a target='_blank' href='https://www.cisecurity.org/insights/blog/getting-to-know-the-cis-benchmarks'>Getting to Know the CIS Benchmarks</a>.

    See: https://schema.ocsf.io/1.6.0/objects/cis_benchmark
    """

    name: str = Field(
        ...,
        description="The CIS Benchmark name. For example: <i>Ensure mounting of cramfs filesystems is disabled.</i>",
    )
    cis_controls: list[CisControl] | None = Field(
        default=None,
        description="The CIS Critical Security Controls is a prioritized set of actions to protect your organization and data from cyber-attack vectors. [Recommended]",
    )
    desc: str | None = Field(
        default=None,
        description="The CIS Benchmark description. For example: <i>The cramfs filesystem type is a compressed read-only Linux filesystem embedded in small footprint systems. A cramfs image can be used without having to first decompress the image.</i>",
    )
