"""Service object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Service(OCSFBaseModel):
    """The Service object describes characteristics of a service, <code> e.g. AWS EC2. </code>

    See: https://schema.ocsf.io/1.2.0/objects/service
    """

    labels: list[str] | None = Field(
        default=None, description="The list of labels associated with the service."
    )
    name: str | None = Field(default=None, description="The name of the service.")
    uid: str | None = Field(default=None, description="The unique identifier of the service.")
    version: str | None = Field(
        default=None, description="The version of the service. [Recommended]"
    )
