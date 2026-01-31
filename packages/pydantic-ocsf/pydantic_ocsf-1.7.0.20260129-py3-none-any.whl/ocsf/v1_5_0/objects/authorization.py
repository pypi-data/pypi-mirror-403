"""Authorization Result object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.objects.policy import Policy


class Authorization(OCSFBaseModel):
    """The Authorization Result object provides details about the authorization outcome and associated policies related to activity.

    See: https://schema.ocsf.io/1.5.0/objects/authorization
    """

    decision: str | None = Field(
        default=None,
        description="Authorization Result/outcome, e.g. allowed, denied. [Recommended]",
    )
    policy: Policy | None = Field(
        default=None,
        description="Details about the Identity/Access management policies that are applicable.",
    )
