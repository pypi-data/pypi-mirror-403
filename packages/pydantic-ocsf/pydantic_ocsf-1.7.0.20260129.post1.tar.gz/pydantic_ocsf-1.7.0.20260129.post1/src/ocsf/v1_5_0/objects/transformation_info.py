"""Transformation Info object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.objects.product import Product


class TransformationInfo(OCSFBaseModel):
    """The transformation_info object represents the mapping or transformation used.

    See: https://schema.ocsf.io/1.5.0/objects/transformation_info
    """

    lang: str | None = Field(
        default=None, description="The transformation language used to transform the data."
    )
    name: str | None = Field(
        default=None, description="The name of the transformation or mapping. [Recommended]"
    )
    product: Product | None = Field(
        default=None, description="The product or instance used to make the transformation"
    )
    time: int | None = Field(default=None, description="Time of the transformation. [Recommended]")
    uid: str | None = Field(
        default=None, description="The unique identifier of the mapping or transformation."
    )
    url_string: Any | None = Field(
        default=None,
        description="The Uniform Resource Locator String where the mapping or transformation exists. [Recommended]",
    )
