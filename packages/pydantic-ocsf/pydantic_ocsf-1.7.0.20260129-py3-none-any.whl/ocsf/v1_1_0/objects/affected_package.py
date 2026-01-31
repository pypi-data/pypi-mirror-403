"""Affected Software Package object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_1_0.objects.remediation import Remediation


class AffectedPackage(OCSFBaseModel):
    """The Affected Package object describes details about a software package identified as affected by a vulnerability/vulnerabilities.

    See: https://schema.ocsf.io/1.1.0/objects/affected_package
    """

    name: str = Field(..., description="The software package name.")
    version: str = Field(..., description="The software package version.")
    architecture: str | None = Field(
        default=None,
        description="Architecture is a shorthand name describing the type of computer hardware the packaged software is meant to run on. [Recommended]",
    )
    epoch: int | None = Field(
        default=None,
        description="The software package epoch. Epoch is a way to define weighted dependencies based on version numbers.",
    )
    fixed_in_version: str | None = Field(
        default=None,
        description="The software package version in which a reported vulnerability was patched/fixed.",
    )
    license: str | None = Field(
        default=None, description="The software license applied to this package."
    )
    package_manager: str | None = Field(
        default=None,
        description="The software packager manager utilized to manage a package on a system, e.g. npm, yum, dpkg etc.",
    )
    path: str | None = Field(
        default=None, description="The installation path of the affected package."
    )
    purl: str | None = Field(
        default=None,
        description="A purl is a URL string used to identify and locate a software package in a mostly universal and uniform way across programming languages, package managers, packaging conventions, tools, APIs and databases.",
    )
    release: str | None = Field(
        default=None,
        description="Release is the number of times a version of the software has been packaged.",
    )
    remediation: Remediation | None = Field(
        default=None,
        description="Describes the recommended remediation steps to address identified issue(s).",
    )
