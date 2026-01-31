"""Databucket object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.enums.type_id import TypeId
    from ocsf.v1_7_0.objects.agent import Agent
    from ocsf.v1_7_0.objects.encryption_details import EncryptionDetails
    from ocsf.v1_7_0.objects.file import File
    from ocsf.v1_7_0.objects.graph import Graph
    from ocsf.v1_7_0.objects.group import Group
    from ocsf.v1_7_0.objects.key_value_object import KeyValueObject
    from ocsf.v1_7_0.objects.user import User


class Databucket(OCSFBaseModel):
    """The databucket object is a basic container that holds data, typically organized through the use of data partitions.

    See: https://schema.ocsf.io/1.7.0/objects/databucket
    """

    type_id: TypeId = Field(..., description="The normalized identifier of the databucket type.")
    agent_list: list[Agent] | None = Field(
        default=None,
        description="A list of <code>agent</code> objects associated with a device, endpoint, or resource.",
    )
    cloud_partition: str | None = Field(
        default=None,
        description="The logical grouping or isolated segment within a cloud provider's infrastructure where the databucket is located.",
    )
    created_time: int | None = Field(
        default=None, description="The time when the databucket was known to have been created."
    )
    criticality: str | None = Field(
        default=None,
        description="The criticality of the databucket as defined by the event source.",
    )
    data: dict[str, Any] | None = Field(
        default=None, description="Additional data describing the resource."
    )
    desc: str | None = Field(default=None, description="The description of the databucket.")
    encryption_details: EncryptionDetails | None = Field(
        default=None,
        description="The encryption details of the databucket. Should be populated if the databucket is encrypted.",
    )
    file: File | None = Field(
        default=None, description="Details about the file/object within a databucket."
    )
    group: Group | None = Field(default=None, description="The name of the related resource group.")
    groups: list[Group] | None = Field(
        default=None, description="The group names to which the databucket belongs."
    )
    hostname: Any | None = Field(
        default=None, description="The fully qualified hostname of the databucket. [Recommended]"
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
    is_encrypted: bool | None = Field(
        default=None, description="Indicates if the databucket is encrypted."
    )
    is_public: bool | None = Field(
        default=None,
        description="Indicates if the databucket is publicly accessible. [Recommended]",
    )
    labels: list[str] | None = Field(
        default=None, description="The list of labels associated to the resource."
    )
    modified_time: int | None = Field(
        default=None,
        description="The most recent time when any changes, updates, or modifications were made within the databucket.",
    )
    name: str | None = Field(default=None, description="The databucket name.")
    namespace: str | None = Field(
        default=None,
        description="The namespace is useful when similar entities exist that you need to keep separate.",
    )
    owner: User | None = Field(
        default=None,
        description="The identity of the service or user account that owns the databucket. [Recommended]",
    )
    region: str | None = Field(default=None, description="The cloud region of the databucket.")
    resource_relationship: Graph | None = Field(
        default=None,
        description="A graph representation showing how this databucket relates to and interacts with other entities in the environment. This can include parent/child relationships, dependencies, or other connections.",
    )
    size: int | None = Field(default=None, description="The size of the databucket in bytes.")
    tags: list[KeyValueObject] | None = Field(
        default=None,
        description="The list of tags; <code>{key:value}</code> pairs associated to the resource.",
    )
    type_: str | None = Field(default=None, description="The databucket type. [Recommended]")
    uid: str | None = Field(default=None, description="The unique identifier of the databucket.")
    uid_alt: Any | None = Field(
        default=None, description="The alternative unique identifier of the resource."
    )
    version: str | None = Field(
        default=None, description="The version of the resource. For example <code>1.2.3</code>."
    )
    zone: str | None = Field(
        default=None,
        description="The specific availability zone within a cloud region where the databucket is located.",
    )
