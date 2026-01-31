"""Software Package object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.type_id import TypeId
    from ocsf.v1_5_0.objects.fingerprint import Fingerprint


class Package(OCSFBaseModel):
    """The Software Package object describes details about a software package.

    See: https://schema.ocsf.io/1.5.0/objects/package
    """

    name: str = Field(..., description="The software package name.")
    version: str = Field(..., description="The software package version.")
    architecture: str | None = Field(
        default=None,
        description="Architecture is a shorthand name describing the type of computer hardware the packaged software is meant to run on. [Recommended]",
    )
    cpe_name: str | None = Field(
        default=None,
        description="The Common Platform Enumeration (CPE) name as described by (<a target='_blank' href='https://nvd.nist.gov/products/cpe'>NIST</a>) For example: <code>cpe:/a:apple:safari:16.2</code>.",
    )
    epoch: int | None = Field(
        default=None,
        description="The software package epoch. Epoch is a way to define weighted dependencies based on version numbers.",
    )
    hash: Fingerprint | None = Field(
        default=None,
        description="Cryptographic hash to identify the binary instance of a software component. This can include any component such file, package, or library.",
    )
    license: str | None = Field(
        default=None, description="The software license applied to this package."
    )
    license_url: Any | None = Field(
        default=None,
        description="The URL pointing to the license applied on package or software. This is typically a <code>LICENSE.md</code> file within a repository.",
    )
    package_manager: str | None = Field(
        default=None,
        description="The software packager manager utilized to manage a package on a system, e.g. npm, yum, dpkg etc.",
    )
    package_manager_url: Any | None = Field(
        default=None,
        description="The URL of the package or library at the package manager, or the specific URL or URI of an internal package manager link such as <code>AWS CodeArtifact</code> or <code>Artifactory</code>.",
    )
    purl: str | None = Field(
        default=None,
        description="A purl is a URL string used to identify and locate a software package in a mostly universal and uniform way across programming languages, package managers, packaging conventions, tools, APIs and databases.",
    )
    release: str | None = Field(
        default=None,
        description="Release is the number of times a version of the software has been packaged.",
    )
    src_url: Any | None = Field(
        default=None,
        description="The link to the specific library or package such as within <code>GitHub</code>, this is different from the link to the package manager where the library or package is hosted.",
    )
    type_: str | None = Field(
        default=None,
        description="The type of software package, normalized to the caption of the <code>type_id</code> value. In the case of 'Other', it is defined by the source.",
    )
    type_id: TypeId | None = Field(
        default=None, description="The type of software package. [Recommended]"
    )
    uid: str | None = Field(
        default=None,
        description="A unique identifier for the package or library reported by the source tool. E.g., the <code>libId</code> within the <code>sbom</code> field of an OX Security Issue or the SPDX <code>components.*.bom-ref</code>.",
    )
    vendor_name: str | None = Field(
        default=None, description="The name of the vendor who published the software package."
    )
