"""Response Elements object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.objects.container import Container


class Response(OCSFBaseModel):
    """The Response Elements object describes characteristics of an API response.

    See: https://schema.ocsf.io/1.6.0/objects/response
    """

    code: int | None = Field(
        default=None, description="The numeric response sent to a request. [Recommended]"
    )
    containers: list[Container] | None = Field(
        default=None,
        description="When working with containerized applications, the set of containers which write to the standard the output of a particular logging driver. For example, this may be the set of containers involved in handling api requests and responses for a containerized application.",
    )
    data: dict[str, Any] | None = Field(
        default=None, description="The additional data that is associated with the api response."
    )
    error: str | None = Field(default=None, description="Error Code [Recommended]")
    error_message: str | None = Field(default=None, description="Error Message [Recommended]")
    flags: list[str] | None = Field(
        default=None,
        description="The communication flags that are associated with the api response.",
    )
    message: str | None = Field(
        default=None,
        description="The description of the event/finding, as defined by the source. [Recommended]",
    )
