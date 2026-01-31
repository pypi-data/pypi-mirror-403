"""Service object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.objects.key_value_object import KeyValueObject


class Service(OCSFBaseModel):
    """The Service object describes characteristics of a service, <code> e.g. AWS EC2. </code>

    See: https://schema.ocsf.io/1.7.0/objects/service
    """

    labels: list[str] | None = Field(
        default=None, description="The list of labels associated with the service."
    )
    name: str | None = Field(default=None, description="The name of the service.")
    tags: list[KeyValueObject] | None = Field(
        default=None,
        description="The list of tags; <code>{key:value}</code> pairs associated to the service.",
    )
    uid: str | None = Field(default=None, description="The unique identifier of the service.")
    version: str | None = Field(
        default=None, description="The version of the service. [Recommended]"
    )
