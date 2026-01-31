"""Policy object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_2_0.objects.group import Group


class Policy(OCSFBaseModel):
    """The Policy object describes the policies that are applicable. <p>Policy attributes provide traceability to the operational state of the security product at the time that the event was captured, facilitating forensics, troubleshooting, and policy tuning/adjustments.</p>

    See: https://schema.ocsf.io/1.2.0/objects/policy
    """

    desc: str | None = Field(default=None, description="The description of the policy.")
    group: Group | None = Field(default=None, description="The policy group.")
    is_applied: bool | None = Field(
        default=None,
        description="A determination if the content of a policy was applied to a target or request, or not.",
    )
    name: str | None = Field(
        default=None, description="The policy name. For example: <code>IAM Policy</code>."
    )
    uid: str | None = Field(default=None, description="A unique identifier of the policy instance.")
    version: str | None = Field(
        default=None, description="The policy version number. [Recommended]"
    )
