"""Resource Details object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_0_0.objects.group import Group
    from ocsf.v1_0_0.objects.user import User


class ResourceDetails(OCSFBaseModel):
    """The Resource Details object describes details about resources that were affected by the activity/event.

    See: https://schema.ocsf.io/1.0.0/objects/resource_details
    """

    cloud_partition: str | None = Field(
        default=None,
        description="The canonical cloud partition name to which the region is assigned (e.g. AWS Partitions: aws, aws-cn, aws-us-gov).",
    )
    criticality: str | None = Field(
        default=None, description="The criticality of the resource as defined by the event source."
    )
    data: dict[str, Any] | None = Field(
        default=None, description="Additional data describing the resource."
    )
    group: Group | None = Field(default=None, description="The name of the related resource group.")
    labels: list[str] | None = Field(
        default=None, description="The list of labels/tags associated to a resource."
    )
    name: str | None = Field(default=None, description="The name of the resource.")
    owner: User | None = Field(
        default=None,
        description="The identity of the service or user account that owns the resource. [Recommended]",
    )
    region: str | None = Field(default=None, description="The cloud region of the resource.")
    type_: str | None = Field(
        default=None, description="The resource type as defined by the event source."
    )
    uid: str | None = Field(default=None, description="The unique identifier of the resource.")
    version: str | None = Field(
        default=None, description="The version of the resource. For example <code>1.2.3</code>."
    )
