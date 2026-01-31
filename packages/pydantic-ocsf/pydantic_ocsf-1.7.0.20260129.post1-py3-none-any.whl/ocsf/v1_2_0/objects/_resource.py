"""Resource object."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Resource(OCSFBaseModel):
    """The Resource object contains attributes that provide information about a particular resource. It serves as a base object, offering attributes that help identify and classify the resource effectively.

    See: https://schema.ocsf.io/1.2.0/objects/_resource
    """

    data: dict[str, Any] | None = Field(
        default=None, description="Additional data describing the resource."
    )
    include: str | None = Field(default=None, description="")
    labels: list[str] | None = Field(
        default=None, description="The list of labels/tags associated to a resource."
    )
    name: str | None = Field(default=None, description="The name of the resource.")
    type_: str | None = Field(
        default=None, description="The resource type as defined by the event source."
    )
    uid: str | None = Field(default=None, description="The unique identifier of the resource.")
