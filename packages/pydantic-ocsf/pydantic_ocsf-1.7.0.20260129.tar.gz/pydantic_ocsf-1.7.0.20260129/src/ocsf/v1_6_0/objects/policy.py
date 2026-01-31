"""Policy object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.objects.group import Group


class Policy(OCSFBaseModel):
    """The Policy object describes the policies that are applicable. <p>Policy attributes provide traceability to the operational state of the security product at the time that the event was captured, facilitating forensics, troubleshooting, and policy tuning/adjustments.</p>

    See: https://schema.ocsf.io/1.6.0/objects/policy
    """

    data: dict[str, Any] | None = Field(
        default=None,
        description="Additional data about the policy such as the underlying JSON policy itself or other details.",
    )
    desc: str | None = Field(default=None, description="The description of the policy.")
    group: Group | None = Field(default=None, description="The policy group.")
    is_applied: bool | None = Field(
        default=None,
        description="A determination if the content of a policy was applied to a target or request, or not. [Recommended]",
    )
    name: str | None = Field(
        default=None,
        description="The policy name. For example: <code>AdministratorAccess Policy</code>.",
    )
    type_: str | None = Field(
        default=None,
        description="The policy type. For example: <code>Identity Policy, Resource Policy, Service Control Policy, etc./code>.",
    )
    uid: str | None = Field(default=None, description="A unique identifier of the policy instance.")
    version: str | None = Field(
        default=None, description="The policy version number. [Recommended]"
    )
