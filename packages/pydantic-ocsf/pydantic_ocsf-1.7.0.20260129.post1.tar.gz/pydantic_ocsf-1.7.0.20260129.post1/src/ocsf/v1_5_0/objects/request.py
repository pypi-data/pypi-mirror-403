"""Request Elements object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.objects.container import Container


class Request(OCSFBaseModel):
    """The Request Elements object describes characteristics of an API request.

    See: https://schema.ocsf.io/1.5.0/objects/request
    """

    uid: str = Field(..., description="The unique request identifier.")
    containers: list[Container] | None = Field(
        default=None,
        description="When working with containerized applications, the set of containers which write to the standard the output of a particular logging driver. For example, this may be the set of containers involved in handling api requests and responses for a containerized application.",
    )
    data: dict[str, Any] | None = Field(
        default=None, description="The additional data that is associated with the api request."
    )
    flags: list[str] | None = Field(
        default=None,
        description="The communication flags that are associated with the api request.",
    )
