"""Permission Analysis Result object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.objects.key_value_object import KeyValueObject
    from ocsf.v1_7_0.objects.policy import Policy


class PermissionAnalysisResult(OCSFBaseModel):
    """The Permission Analysis object describes analysis results of permissions, policies directly associated with an identity (user, role, or service account). This evaluates what permissions an identity has been granted through attached policies, which privileges are actively used versus unused, and identifies potential over-privileged access. Use this for identity-centric security assessments such as privilege audits, dormant permission discovery, and least-privilege compliance analysis.

    See: https://schema.ocsf.io/1.7.0/objects/permission_analysis_result
    """

    condition_keys: list[KeyValueObject] | None = Field(
        default=None,
        description="The condition keys and their values that were evaluated during policy analysis, including contextual constraints that affect permission grants. These conditions define when and how permissions are applied. Examples: <code>aws:SourceIp:1.2.3.4</code>, <code>aws:RequestedRegion:us-east-1</code>.",
    )
    granted_privileges: list[str] | None = Field(
        default=None,
        description="The specific privileges, actions, or permissions that are explicitly granted by the analyzed policy. Examples: AWS actions like <code>s3:GetObject</code>, <code>ec2:RunInstances</code>, <code>iam:CreateUser</code>; Azure actions like <code>Microsoft.Storage/storageAccounts/read</code>; or GCP permissions like <code>storage.objects.get</code>.",
    )
    policy: Policy | None = Field(
        default=None,
        description="Detailed information about the policy document that was analyzed, including policy metadata, version, type (identity-based, resource-based, etc.), and structural details. This provides context for understanding the scope and nature of the permission analysis. [Recommended]",
    )
    unused_privileges_count: int | None = Field(
        default=None,
        description="The total count of privileges or actions defined in the policy that have not been utilized within the analysis timeframe. This metric helps identify over-privileged access and opportunities for privilege reduction to follow the principle of least privilege. High counts may indicate policy bloat or excessive permissions.",
    )
    unused_services_count: int | None = Field(
        default=None,
        description="The total count of cloud services or resource types referenced in the policy that have not been accessed or utilized within the analysis timeframe. This helps identify unused service permissions that could be removed to reduce attack surface. Examples: AWS services like S3, SQS, IAM, Lambda; Azure services like Storage, Compute, KeyVault; or GCP services like Cloud Storage, Compute Engine, BigQuery.",
    )
