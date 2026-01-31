"""Web Resource object."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ocsf._base import OCSFBaseModel


class WebResource(OCSFBaseModel):
    """The Web Resource object describes characteristics of a web resource that was affected by the activity/event.

    See: https://schema.ocsf.io/1.2.0/objects/web_resource
    """

    data: dict[str, Any] | None = Field(
        default=None,
        description="Details of the web resource, e.g, <code>file</code> details, <code>search</code> results or application-defined resource.",
    )
    desc: str | None = Field(default=None, description="Description of the web resource.")
    include: str | None = Field(default=None, description="")
    labels: list[str] | None = Field(
        default=None, description="The list of labels/tags associated to a resource."
    )
    name: str | None = Field(default=None, description="The name of the web resource.")
    type_: str | None = Field(
        default=None, description="The web resource type as defined by the event source."
    )
    uid: str | None = Field(default=None, description="The unique identifier of the web resource.")
    url_string: Any | None = Field(
        default=None,
        description="The URL pointing towards the source of the web resource. [Recommended]",
    )
