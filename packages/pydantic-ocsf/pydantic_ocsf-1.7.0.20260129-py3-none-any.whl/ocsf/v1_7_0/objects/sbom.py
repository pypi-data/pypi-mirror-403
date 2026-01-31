"""Software Bill of Materials object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.enums.type_id import TypeId
    from ocsf.v1_7_0.objects.package import Package
    from ocsf.v1_7_0.objects.product import Product
    from ocsf.v1_7_0.objects.software_component import SoftwareComponent


class Sbom(OCSFBaseModel):
    """The Software Bill of Materials object describes characteristics of a generated SBOM.

    See: https://schema.ocsf.io/1.7.0/objects/sbom
    """

    package: Package = Field(
        ...,
        description="The software package or library that is being discovered or inventoried by an SBOM.",
    )
    software_components: list[SoftwareComponent] = Field(
        ..., description="The list of software components used in the software package."
    )
    created_time: int | None = Field(
        default=None, description="The time when the SBOM was created. [Recommended]"
    )
    product: Product | None = Field(
        default=None,
        description="Details about the upstream product that generated the SBOM e.g. <code>cdxgen</code> or <code>Syft</code>. [Recommended]",
    )
    type_: str | None = Field(
        default=None,
        description="The type of SBOM, normalized to the caption of the <code>type_id</code> value. In the case of 'Other', it is defined by the source.",
    )
    type_id: TypeId | None = Field(default=None, description="The type of SBOM. [Recommended]")
    uid: str | None = Field(
        default=None,
        description="A unique identifier for the SBOM or the SBOM generation by a source tool, such as the SPDX <code>metadata.component.bom-ref</code>.",
    )
    version: str | None = Field(
        default=None,
        description="The specification (spec) version of the particular SBOM, e.g., <code>1.6</code>.",
    )
