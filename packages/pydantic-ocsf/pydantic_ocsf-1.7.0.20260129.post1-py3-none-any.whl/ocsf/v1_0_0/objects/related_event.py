"""Related Event object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class RelatedEvent(OCSFBaseModel):
    """The Related Event object describes an event related to a finding or detection as identified by the security product.

    See: https://schema.ocsf.io/1.0.0/objects/related_event
    """

    uid: str = Field(..., description="The unique identifier of the related event.")
    product_uid: str | None = Field(
        default=None,
        description="The unique identifier of the product that reported the related event.",
    )
    type_: str | None = Field(
        default=None,
        description="The type of the related event. For example: Process Activity: Launch.",
    )
    type_uid: int | None = Field(
        default=None,
        description="The unique identifier of the related event type. For example: 100701. [Recommended]",
    )
