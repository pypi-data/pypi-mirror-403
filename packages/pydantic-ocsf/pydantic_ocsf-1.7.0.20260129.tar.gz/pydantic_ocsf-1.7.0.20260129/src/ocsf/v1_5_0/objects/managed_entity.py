"""Managed Entity object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.type_id import TypeId
    from ocsf.v1_5_0.objects.device import Device
    from ocsf.v1_5_0.objects.email import Email
    from ocsf.v1_5_0.objects.group import Group
    from ocsf.v1_5_0.objects.location import Location
    from ocsf.v1_5_0.objects.organization import Organization
    from ocsf.v1_5_0.objects.policy import Policy
    from ocsf.v1_5_0.objects.user import User


class ManagedEntity(OCSFBaseModel):
    """The Managed Entity object describes the type and version of an entity, such as a user, device, or policy.  For types in the <code>type_id</code> enum list, an associated attribute should be populated.  If the type of entity is not in the <code>type_id</code> list, information can be put into the <code>data</code> attribute, <code>type_id</code> should be 'Other' and the <code>type</code> attribute should label the entity type.

    See: https://schema.ocsf.io/1.5.0/objects/managed_entity
    """

    data: dict[str, Any] | None = Field(
        default=None, description="The managed entity content as a JSON object."
    )
    device: Device | None = Field(
        default=None, description="An addressable device, computer system or host. [Recommended]"
    )
    email: Email | None = Field(default=None, description="The email object. [Recommended]")
    group: Group | None = Field(
        default=None,
        description="The group object associated with an entity such as user, policy, or rule. [Recommended]",
    )
    location: Location | None = Field(
        default=None,
        description="The detailed geographical location usually associated with an IP address.",
    )
    name: str | None = Field(
        default=None,
        description="The name of the managed entity. It should match the name of the specific entity object's name if populated, or the name of the managed entity if the <code>type_id</code> is 'Other'.",
    )
    org: Organization | None = Field(
        default=None,
        description="Organization and org unit relevant to the event or object. [Recommended]",
    )
    policy: Policy | None = Field(
        default=None, description="Describes details of a managed policy. [Recommended]"
    )
    type_: str | None = Field(
        default=None,
        description="The managed entity type. For example: <code>Policy</code>, <code>User</code>, <code>Organization</code>, <code>Device</code>. [Recommended]",
    )
    type_id: TypeId | None = Field(
        default=None,
        description="The type of the Managed Entity. It is recommended to also populate the <code>type</code> attribute with the associated label, or the source specific name if <code>Other</code>. [Recommended]",
    )
    uid: str | None = Field(
        default=None,
        description="The identifier of the managed entity. It should match the <code>uid</code> of the specific entity's object UID if populated, or the source specific ID if the <code>type_id</code> is 'Other'.",
    )
    user: User | None = Field(
        default=None, description="The user that pertains to the event or object. [Recommended]"
    )
    version: str | None = Field(
        default=None,
        description="The version of the managed entity. For example: <code>1.2.3</code>. [Recommended]",
    )
