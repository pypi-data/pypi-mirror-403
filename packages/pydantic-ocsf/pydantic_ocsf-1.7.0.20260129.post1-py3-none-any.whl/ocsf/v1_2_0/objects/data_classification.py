"""Data Classification object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_2_0.enums.category_id import CategoryId
    from ocsf.v1_2_0.enums.confidentiality_id import ConfidentialityId
    from ocsf.v1_2_0.objects.policy import Policy


class DataClassification(OCSFBaseModel):
    """The Data Classification object includes information about data classification levels and data category types.

    See: https://schema.ocsf.io/1.2.0/objects/data_classification
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
    policy: Policy | None = Field(
        default=None,
        description="Details about the data policy that governs data handling and security measures related to classification.",
    )
