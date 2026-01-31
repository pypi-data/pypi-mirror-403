"""Resource object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.objects.key_value_object import KeyValueObject


class Resource(OCSFBaseModel):
    """The Resource object contains attributes that provide information about a particular resource. It serves as a base object, offering attributes that help identify and classify the resource effectively.

    See: https://schema.ocsf.io/1.5.0/objects/_resource
    """

    created_time: int | None = Field(
        default=None, description="The time when the resource was created."
    )
    data: dict[str, Any] | None = Field(
        default=None, description="Additional data describing the resource."
    )
    include: str | None = Field(default=None, description="")
    labels: list[str] | None = Field(
        default=None, description="The list of labels associated to the resource."
    )
    modified_time: int | None = Field(
        default=None, description="The time when the resource was last modified."
    )
    name: str | None = Field(default=None, description="The name of the resource.")
    tags: list[KeyValueObject] | None = Field(
        default=None,
        description="The list of tags; <code>{key:value}</code> pairs associated to the resource.",
    )
    type_: str | None = Field(
        default=None, description="The resource type as defined by the event source."
    )
    uid: Any | None = Field(default=None, description="The unique identifier of the resource.")
    uid_alt: Any | None = Field(
        default=None, description="The alternative unique identifier of the resource."
    )
