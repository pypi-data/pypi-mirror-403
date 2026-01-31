"""Data Security object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_2_0.enums.category_id import CategoryId
    from ocsf.v1_2_0.enums.confidentiality_id import ConfidentialityId
    from ocsf.v1_2_0.enums.data_lifecycle_state_id import DataLifecycleStateId
    from ocsf.v1_2_0.enums.detection_system_id import DetectionSystemId
    from ocsf.v1_2_0.objects.policy import Policy


class DataSecurity(OCSFBaseModel):
    """The Data Security object describes the characteristics, techniques and content of a Data Loss Prevention (DLP), Data Loss Detection (DLD), Data Classification, or similar tools' finding, alert, or detection mechanism(s).

    See: https://schema.ocsf.io/1.2.0/objects/data_security
    """

    category: str | None = Field(
        default=None,
        description="The name of the data classification category that data matched into, e.g. Financial, Personal, Governmental, etc.",
    )
    category_id: CategoryId | None = Field(
        default=None,
        description="The normalized identifier of the data classification category. [Recommended]",
    )
    confidentiality: str | None = Field(
        default=None,
        description="The file content confidentiality, normalized to the confidentiality_id value. In the case of 'Other', it is defined by the event source.",
    )
    confidentiality_id: ConfidentialityId | None = Field(
        default=None,
        description="The normalized identifier of the file content confidentiality indicator. [Recommended]",
    )
    data_lifecycle_state: str | None = Field(
        default=None,
        description="The name of the stage or state that the data was in. E.g., Data-at-Rest, Data-in-Transit, etc.",
    )
    data_lifecycle_state_id: DataLifecycleStateId | None = Field(
        default=None,
        description="The stage or state that the data was in when it was assessed or scanned by a data security tool. [Recommended]",
    )
    detection_pattern: str | None = Field(
        default=None,
        description="Specific pattern, algorithm, fingerpint, or model used for detection. [Recommended]",
    )
    detection_system: str | None = Field(
        default=None,
        description="The name of the type of data security tool or system that the finding, detection, or alert originated from. E.g., Endpoint, Secure Email Gateway, etc.",
    )
    detection_system_id: DetectionSystemId | None = Field(
        default=None,
        description="The type of data security tool or system that the finding, detection, or alert originated from. [Recommended]",
    )
    pattern_match: str | None = Field(
        default=None,
        description="A text, binary, file name, or datastore that matched against a detection rule.",
    )
    policy: Policy | None = Field(
        default=None,
        description="Details about the policy that triggered the finding. [Recommended]",
    )
