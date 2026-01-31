"""Assessment object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.objects.policy import Policy


class Assessment(OCSFBaseModel):
    """The Assessment object describes a point-in-time assessment, check, or evaluation of a specific configuration or signal against an asset, entity, person, or otherwise. For example, this can encapsulate <code>os_signals</code> from CrowdStrike Falcon Zero Trust Assessments, or account for <code>Datastore</code> configurations from Cyera, or capture details of Microsoft Intune configuration policies.

    See: https://schema.ocsf.io/1.5.0/objects/assessment
    """

    meets_criteria: bool = Field(
        ...,
        description="Determines whether the assessment against the specific configuration or signal meets the assessments criteria. For example, if the assessment checks if a <code>Datastore</code> is encrypted or not, having encryption would be evaluated as <code>true</code>.",
    )
    category: str | None = Field(
        default=None,
        description="The category that the assessment is part of. For example: <code>Prevention</code> or <code>Windows 10</code>.",
    )
    desc: str | None = Field(
        default=None,
        description="The description of the assessment criteria, or a description of the specific configuration or signal the assessment is targeting. [Recommended]",
    )
    name: str | None = Field(
        default=None,
        description="The name of the configuration or signal being assessed. For example: <code>Kernel Mode Code Integrity (KMCI)</code> or <code>publicAccessibilityState</code>. [Recommended]",
    )
    policy: Policy | None = Field(
        default=None, description="The details of any policy associated with an assessment."
    )
    uid: str | None = Field(
        default=None,
        description="The unique identifier of the configuration or signal being assessed. For example: the <code>signal_id</code>.",
    )
