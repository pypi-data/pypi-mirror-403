"""Software Package object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Package(OCSFBaseModel):
    """The Software Package object describes details about a software package. Defined by D3FEND <a target='_blank' href='https://d3fend.mitre.org/dao/artifact/d3f:SoftwarePackage/'>d3f:SoftwarePackage</a>.

    See: https://schema.ocsf.io/1.2.0/objects/package
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
    license: str | None = Field(
        default=None, description="The software license applied to this package."
    )
    purl: str | None = Field(
        default=None,
        description="A purl is a URL string used to identify and locate a software package in a mostly universal and uniform way across programming languages, package managers, packaging conventions, tools, APIs and databases.",
    )
    release: str | None = Field(
        default=None,
        description="Release is the number of times a version of the software has been packaged.",
    )
