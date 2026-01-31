"""Image object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.objects.key_value_object import KeyValueObject


class Image(OCSFBaseModel):
    """The Image object provides a description of a specific Virtual Machine (VM) or Container image.

    See: https://schema.ocsf.io/1.6.0/objects/image
    """

    uid: str = Field(
        ..., description="The unique image ID. For example: <code>77af4d6b9913</code>."
    )
    labels: list[str] | None = Field(
        default=None, description="The list of labels associated to the image."
    )
    name: str | None = Field(
        default=None, description="The image name. For example: <code>elixir</code>."
    )
    path: Any | None = Field(default=None, description="The full path to the image file.")
    tag: str | None = Field(
        default=None, description="The image tag. For example: <code>1.11-alpine</code>."
    )
    tags: list[KeyValueObject] | None = Field(
        default=None,
        description="The list of tags; <code>{key:value}</code> pairs associated to the image.",
    )
