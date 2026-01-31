"""Data Classification object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.category_id import CategoryId
    from ocsf.v1_5_0.enums.confidentiality_id import ConfidentialityId
    from ocsf.v1_5_0.enums.status_id import StatusId
    from ocsf.v1_5_0.objects.classifier_details import ClassifierDetails
    from ocsf.v1_5_0.objects.discovery_details import DiscoveryDetails
    from ocsf.v1_5_0.objects.policy import Policy


class DataClassification(OCSFBaseModel):
    """The Data Classification object includes information about data classification levels and data category types.

    See: https://schema.ocsf.io/1.5.0/objects/data_classification
    """

    category: str | None = Field(
        default=None,
        description="The name of the data classification category that data matched into, e.g. Financial, Personal, Governmental, etc.",
    )
    category_id: CategoryId | None = Field(
        default=None,
        description="The normalized identifier of the data classification category. [Recommended]",
    )
    classifier_details: ClassifierDetails | None = Field(
        default=None,
        description="Describes details about the classifier used for data classification. [Recommended]",
    )
    confidentiality: str | None = Field(
        default=None,
        description="The file content confidentiality, normalized to the confidentiality_id value. In the case of 'Other', it is defined by the event source.",
    )
    confidentiality_id: ConfidentialityId | None = Field(
        default=None,
        description="The normalized identifier of the file content confidentiality indicator. [Recommended]",
    )
    discovery_details: list[DiscoveryDetails] | None = Field(
        default=None, description="Details about the data discovered by classification job."
    )
    policy: Policy | None = Field(
        default=None,
        description="Details about the data policy that governs data handling and security measures related to classification.",
    )
    size: int | None = Field(default=None, description="Size of the data classified.")
    src_url: Any | None = Field(
        default=None,
        description="The source URL pointing towards the full classifcation job details.",
    )
    status: str | None = Field(
        default=None,
        description="The resultant status of the classification job normalized to the caption of the <code>status_id</code> value. In the case of 'Other', it is defined by the event source. [Recommended]",
    )
    status_details: list[str] | None = Field(
        default=None,
        description="The contextual description of the <code>status, status_id</code> value.",
    )
    status_id: StatusId | None = Field(
        default=None,
        description="The normalized status identifier of the classification job. [Recommended]",
    )
    total: int | None = Field(
        default=None,
        description="The total count of discovered entities, by the classification job.",
    )
    uid: str | None = Field(
        default=None, description="The unique identifier of the classification job."
    )
