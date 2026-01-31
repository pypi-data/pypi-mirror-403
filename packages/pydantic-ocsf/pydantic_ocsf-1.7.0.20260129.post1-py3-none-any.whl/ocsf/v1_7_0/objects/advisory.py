"""Advisory object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.enums.install_state_id import InstallStateId
    from ocsf.v1_7_0.objects.cve import Cve
    from ocsf.v1_7_0.objects.cwe import Cwe
    from ocsf.v1_7_0.objects.os import Os
    from ocsf.v1_7_0.objects.product import Product
    from ocsf.v1_7_0.objects.timespan import Timespan


class Advisory(OCSFBaseModel):
    """The Advisory object represents publicly disclosed cybersecurity vulnerabilities defined in a Security advisory. e.g. <code> Microsoft KB Article</code>, <code>Apple Security Advisory</code>, or a <code>GitHub Security Advisory (GHSA)</code>

    See: https://schema.ocsf.io/1.7.0/objects/advisory
    """

    uid: str = Field(
        ...,
        description="The unique identifier assigned to the advisory or disclosed vulnerability, e.g, <code>GHSA-5mrr-rgp6-x4gr</code>.",
    )
    avg_timespan: Timespan | None = Field(default=None, description="The average time to patch.")
    bulletin: str | None = Field(default=None, description="The Advisory bulletin identifier.")
    classification: str | None = Field(
        default=None, description="The vendors classification of the Advisory."
    )
    created_time: int | None = Field(
        default=None, description="The time when the Advisory record was created. [Recommended]"
    )
    desc: str | None = Field(
        default=None, description="A brief description of the Advisory Record."
    )
    install_state: str | None = Field(
        default=None, description="The install state of the Advisory. [Recommended]"
    )
    install_state_id: InstallStateId | None = Field(
        default=None, description="The normalized install state ID of the Advisory. [Recommended]"
    )
    is_superseded: bool | None = Field(
        default=None, description="The Advisory has been replaced by another."
    )
    modified_time: int | None = Field(
        default=None, description="The time when the Advisory record was last updated."
    )
    os: Os | None = Field(
        default=None, description="The operating system the Advisory applies to. [Recommended]"
    )
    product: Product | None = Field(
        default=None, description="The product where the vulnerability was discovered."
    )
    references: list[str] | None = Field(
        default=None,
        description="A list of reference URLs with additional information about the vulnerabilities disclosed in the Advisory. [Recommended]",
    )
    related_cves: list[Cve] | None = Field(
        default=None,
        description="A list of Common Vulnerabilities and Exposures <a target='_blank' href='https://cve.mitre.org/'>(CVE)</a> identifiers related to the vulnerabilities disclosed in the Advisory.",
    )
    related_cwes: list[Cwe] | None = Field(
        default=None,
        description="A list of Common Weakness Enumeration <a target='_blank' href='https://cwe.mitre.org/'>(CWE)</a> identifiers related to the vulnerabilities disclosed in the Advisory.",
    )
    size: int | None = Field(
        default=None,
        description="The size in bytes for the Advisory. Usually populated for a KB Article patch.",
    )
    src_url: Any | None = Field(
        default=None, description="The Advisory link from the source vendor."
    )
    title: str | None = Field(
        default=None,
        description="A title or a brief phrase summarizing the Advisory. [Recommended]",
    )
