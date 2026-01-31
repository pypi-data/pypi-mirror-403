"""KB Article object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.install_state_id import InstallStateId
    from ocsf.v1_5_0.objects.os import Os
    from ocsf.v1_5_0.objects.product import Product
    from ocsf.v1_5_0.objects.timespan import Timespan


class KbArticle(OCSFBaseModel):
    """The KB Article object contains metadata that describes the patch or update.

    See: https://schema.ocsf.io/1.5.0/objects/kb_article
    """

    uid: str = Field(..., description="The unique identifier for the kb article.")
    avg_timespan: Timespan | None = Field(default=None, description="The average time to patch.")
    bulletin: str | None = Field(default=None, description="The kb article bulletin identifier.")
    classification: str | None = Field(
        default=None, description="The vendors classification of the kb article."
    )
    created_time: int | None = Field(
        default=None, description="The date the kb article was released by the vendor."
    )
    install_state: str | None = Field(
        default=None, description="The install state of the kb article. [Recommended]"
    )
    install_state_id: InstallStateId | None = Field(
        default=None, description="The normalized install state ID of the kb article. [Recommended]"
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
