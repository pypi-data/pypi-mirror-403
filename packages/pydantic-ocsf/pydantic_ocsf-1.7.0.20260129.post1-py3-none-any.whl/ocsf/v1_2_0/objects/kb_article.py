"""KB Article object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_2_0.objects.os import Os
    from ocsf.v1_2_0.objects.product import Product


class KbArticle(OCSFBaseModel):
    """The KB Article object contains metadata that describes the patch or update.

    See: https://schema.ocsf.io/1.2.0/objects/kb_article
    """

    uid: str = Field(..., description="The unique identifier for the kb article.")
    bulletin: str | None = Field(default=None, description="The kb article bulletin identifier.")
    classification: str | None = Field(
        default=None, description="The vendors classification of the kb article."
    )
    created_time: int | None = Field(
        default=None, description="The date the kb article was released by the vendor."
    )
    is_superseded: bool | None = Field(
        default=None, description="The kb article has been replaced by another."
    )
    os: Os | None = Field(
        default=None, description="The operating system the kb article applies. [Recommended]"
    )
    product: Product | None = Field(
        default=None, description="The product details the kb article applies."
    )
    severity: str | None = Field(
        default=None, description="The severity of the kb article. [Recommended]"
    )
    size: int | None = Field(default=None, description="The size in bytes for the kb article.")
    src_url: Any | None = Field(
        default=None, description="The kb article link from the source vendor."
    )
    title: str | None = Field(
        default=None, description="The title of the kb article. [Recommended]"
    )
