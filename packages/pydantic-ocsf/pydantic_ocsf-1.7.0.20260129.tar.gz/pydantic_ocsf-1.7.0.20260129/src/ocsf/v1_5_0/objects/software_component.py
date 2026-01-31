"""Software Component object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.relationship_id import RelationshipId
    from ocsf.v1_5_0.enums.type_id import TypeId
    from ocsf.v1_5_0.objects.fingerprint import Fingerprint


class SoftwareComponent(OCSFBaseModel):
    """The Software Component object describes characteristics of a software component within a software package.

    See: https://schema.ocsf.io/1.5.0/objects/software_component
    """

    name: str = Field(..., description="The software component name.")
    version: str = Field(..., description="The software component version.")
    author: str | None = Field(
        default=None,
        description="The author(s) who published the software component. [Recommended]",
    )
    hash: Fingerprint | None = Field(
        default=None,
        description="Cryptographic hash to identify the binary instance of a software component.",
    )
    license: str | None = Field(
        default=None, description="The software license applied to this component."
    )
    purl: str | None = Field(
        default=None,
        description="The Package URL (PURL) to identify the software component. This is a URL that uniquely identifies the component, including the component's name, version, and type. The URL is used to locate and retrieve the component's metadata and content. [Recommended]",
    )
    related_component: str | None = Field(
        default=None,
        description="The package URL (PURL) of the component that this software component has a relationship with. [Recommended]",
    )
    relationship: str | None = Field(
        default=None,
        description="The relationship between two software components, normalized to the caption of the <code>relationship_id</code> value. In the case of 'Other', it is defined by the source.",
    )
    relationship_id: RelationshipId | None = Field(
        default=None,
        description="The normalized identifier of the relationship between two software components. [Recommended]",
    )
    type_: str | None = Field(
        default=None,
        description="The type of software component, normalized to the caption of the <code>type_id</code> value. In the case of 'Other', it is defined by the source.",
    )
    type_id: TypeId | None = Field(
        default=None, description="The type of software component. [Recommended]"
    )
