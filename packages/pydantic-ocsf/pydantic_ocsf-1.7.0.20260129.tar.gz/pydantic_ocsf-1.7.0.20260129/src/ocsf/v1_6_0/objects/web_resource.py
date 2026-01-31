"""Web Resource object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.objects.key_value_object import KeyValueObject


class WebResource(OCSFBaseModel):
    """The Web Resource object describes characteristics of a web resource that was affected by the activity/event.

    See: https://schema.ocsf.io/1.6.0/objects/web_resource
    """

    created_time: int | None = Field(
        default=None, description="The time when the resource was created."
    )
    data: dict[str, Any] | None = Field(
        default=None,
        description="Details of the web resource, e.g, <code>file</code> details, <code>search</code> results or application-defined resource.",
    )
    desc: str | None = Field(default=None, description="Description of the web resource.")
    include: str | None = Field(default=None, description="")
    labels: list[str] | None = Field(
        default=None, description="The list of labels associated to the resource."
    )
    modified_time: int | None = Field(
        default=None, description="The time when the resource was last modified."
    )
    name: str | None = Field(default=None, description="The name of the web resource.")
    tags: list[KeyValueObject] | None = Field(
        default=None,
        description="The list of tags; <code>{key:value}</code> pairs associated to the resource.",
    )
    type_: str | None = Field(
        default=None, description="The web resource type as defined by the event source."
    )
    uid: str | None = Field(default=None, description="The unique identifier of the web resource.")
    uid_alt: Any | None = Field(
        default=None, description="The alternative unique identifier of the resource."
    )
    url_string: Any | None = Field(
        default=None,
        description="The URL pointing towards the source of the web resource. [Recommended]",
    )
