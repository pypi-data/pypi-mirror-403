"""API object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.objects.group import Group
    from ocsf.v1_6_0.objects.request import Request
    from ocsf.v1_6_0.objects.response import Response
    from ocsf.v1_6_0.objects.service import Service


class Api(OCSFBaseModel):
    """The API, or Application Programming Interface, object represents  information pertaining to an API request and response.

    See: https://schema.ocsf.io/1.6.0/objects/api
    """

    operation: str = Field(..., description="Verb/Operation associated with the request")
    group: Group | None = Field(
        default=None, description="The information pertaining to the API group."
    )
    request: Request | None = Field(
        default=None, description="Details pertaining to the API request. [Recommended]"
    )
    response: Response | None = Field(
        default=None, description="Details pertaining to the API response. [Recommended]"
    )
    service: Service | None = Field(
        default=None, description="The information pertaining to the API service."
    )
    version: str | None = Field(default=None, description="The version of the API service.")
