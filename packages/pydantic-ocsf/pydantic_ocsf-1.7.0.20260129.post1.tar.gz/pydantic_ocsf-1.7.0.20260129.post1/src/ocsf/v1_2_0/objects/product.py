"""Product object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_2_0.objects.feature import Feature


class Product(OCSFBaseModel):
    """The Product object describes characteristics of a software product.

    See: https://schema.ocsf.io/1.2.0/objects/product
    """

    vendor_name: str = Field(..., description="The name of the vendor of the product.")
    cpe_name: str | None = Field(
        default=None,
        description="The Common Platform Enumeration (CPE) name as described by (<a target='_blank' href='https://nvd.nist.gov/products/cpe'>NIST</a>) For example: <code>cpe:/a:apple:safari:16.2</code>.",
    )
    feature: Feature | None = Field(
        default=None, description="The feature that reported the event."
    )
    include: str | None = Field(default=None, description="")
    lang: str | None = Field(
        default=None,
        description="The two letter lower case language codes, as defined by <a target='_blank' href='https://en.wikipedia.org/wiki/ISO_639-1'>ISO 639-1</a>. For example: <code>en</code> (English), <code>de</code> (German), or <code>fr</code> (French).",
    )
    name: str | None = Field(default=None, description="The name of the product.")
    path: str | None = Field(default=None, description="The installation path of the product.")
    uid: str | None = Field(default=None, description="The unique identifier of the product.")
    url_string: Any | None = Field(
        default=None, description="The URL pointing towards the product."
    )
    version: str | None = Field(
        default=None,
        description="The version of the product, as defined by the event source. For example: <code>2013.1.3-beta</code>. [Recommended]",
    )
