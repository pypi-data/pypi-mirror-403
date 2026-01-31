"""Image object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Image(OCSFBaseModel):
    """The Image object provides a description of a specific Virtual Machine (VM) or Container image. Defined by D3FEND <a target='_blank' href='https://d3fend.mitre.org/dao/artifact/d3f:ContainerImage/'>d3f:ContainerImage</a>.

    See: https://schema.ocsf.io/1.1.0/objects/image
    """

    uid: str = Field(
        ..., description="The unique image ID. For example: <code>77af4d6b9913</code>."
    )
    labels: list[str] | None = Field(default=None, description="The image labels.")
    name: str | None = Field(
        default=None, description="The image name. For example: <code>elixir</code>."
    )
    path: str | None = Field(default=None, description="The full path to the image file.")
    tag: str | None = Field(
        default=None, description="The image tag. For example: <code>1.11-alpine</code>."
    )
