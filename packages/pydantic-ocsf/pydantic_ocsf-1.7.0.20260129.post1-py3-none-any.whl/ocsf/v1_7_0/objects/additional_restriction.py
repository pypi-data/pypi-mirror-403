"""Additional Restriction object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.enums.status_id import StatusId
    from ocsf.v1_7_0.objects.policy import Policy


class AdditionalRestriction(OCSFBaseModel):
    """The Additional Restriction object describes supplementary access controls and guardrails that constrain or limit granted permissions beyond the primary policy. These restrictions are typically applied through hierarchical policy frameworks, organizational controls, or conditional access mechanisms. Examples include AWS Service Control Policies (SCPs), Resource Control Policies (RCPs), Azure Management Group policies, GCP Organization policies, conditional access policies, IP restrictions, time-based constraints, and MFA requirements.

    See: https://schema.ocsf.io/1.7.0/objects/additional_restriction
    """

    policy: Policy = Field(
        ...,
        description="Detailed information about the policy document that defines this restriction, including policy metadata, type, scope, and the specific rules or conditions that implement the access control.",
    )
    status: str | None = Field(
        default=None,
        description="The current status of the policy restriction, normalized to the caption of the <code>status_id</code> enum value.",
    )
    status_id: StatusId | None = Field(
        default=None,
        description="The normalized status identifier indicating the applicability of this policy restriction. [Recommended]",
    )
