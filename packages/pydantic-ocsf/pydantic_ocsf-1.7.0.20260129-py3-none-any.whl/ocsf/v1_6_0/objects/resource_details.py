"""Resource Details object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.enums.role_id import RoleId
    from ocsf.v1_6_0.objects.agent import Agent
    from ocsf.v1_6_0.objects.graph import Graph
    from ocsf.v1_6_0.objects.group import Group
    from ocsf.v1_6_0.objects.key_value_object import KeyValueObject
    from ocsf.v1_6_0.objects.user import User


class ResourceDetails(OCSFBaseModel):
    """The Resource Details object describes details about resources that were affected by the activity/event.

    See: https://schema.ocsf.io/1.6.0/objects/resource_details
    """

    agent_list: list[Agent] | None = Field(
        default=None,
        description="A list of <code>agent</code> objects associated with a device, endpoint, or resource.",
    )
    cloud_partition: str | None = Field(
        default=None,
        description="The canonical cloud partition name to which the region is assigned (e.g. AWS Partitions: aws, aws-cn, aws-us-gov).",
    )
    created_time: int | None = Field(
        default=None, description="The time when the resource was created."
    )
    criticality: str | None = Field(
        default=None, description="The criticality of the resource as defined by the event source."
    )
    data: dict[str, Any] | None = Field(
        default=None, description="Additional data describing the resource."
    )
    group: Group | None = Field(default=None, description="The name of the related resource group.")
    hostname: Any | None = Field(
        default=None, description="The fully qualified name of the resource. [Recommended]"
    )
    include: str | None = Field(default=None, description="")
    ip: Any | None = Field(
        default=None,
        description="The IP address of the resource, in either IPv4 or IPv6 format. [Recommended]",
    )
    is_backed_up: bool | None = Field(
        default=None,
        description="Indicates whether the device or resource has a backup enabled, such as an automated snapshot or a cloud backup. For example, this is indicated by the <code>cloudBackupEnabled</code> value within JAMF Pro mobile devices or the registration of an AWS ARN with the AWS Backup service.",
    )
    labels: list[str] | None = Field(
        default=None, description="The list of labels associated to the resource."
    )
    modified_time: int | None = Field(
        default=None, description="The time when the resource was last modified."
    )
    name: str | None = Field(
        default=None, description="The name of the entity. See specific usage. [Recommended]"
    )
    namespace: str | None = Field(
        default=None,
        description="The namespace is useful when similar entities exist that you need to keep separate.",
    )
    owner: User | None = Field(
        default=None,
        description="The identity of the service or user account that owns the resource. [Recommended]",
    )
    region: str | None = Field(default=None, description="The cloud region of the resource.")
    resource_relationship: Graph | None = Field(
        default=None,
        description="A graph representation showing how this resource relates to and interacts with other entities in the environment. This can include parent/child relationships, dependencies, or other connections.",
    )
    role: str | None = Field(
        default=None,
        description="The role of the resource in the context of the event or finding, normalized to the caption of the role_id value. In the case of 'Other', it is defined by the event source.",
    )
    role_id: RoleId | None = Field(
        default=None,
        description="The normalized identifier of the resource's role in the context of the event or finding. [Recommended]",
    )
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
    version: str | None = Field(
        default=None, description="The version of the resource. For example <code>1.2.3</code>."
    )
    zone: str | None = Field(
        default=None,
        description="The specific availability zone within a cloud region where the resource is located.",
    )
