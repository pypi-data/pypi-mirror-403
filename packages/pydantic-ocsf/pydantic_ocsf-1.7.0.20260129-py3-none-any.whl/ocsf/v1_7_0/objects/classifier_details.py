"""Classifier Details object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class ClassifierDetails(OCSFBaseModel):
    """The Classifier Details object describes details about the classifier used for data classification.

    See: https://schema.ocsf.io/1.7.0/objects/classifier_details
    """

    type_: str = Field(..., description="The type of the classifier.")
    name: str | None = Field(default=None, description="The name of the classifier. [Recommended]")
    uid: str | None = Field(
        default=None, description="The unique identifier of the classifier. [Recommended]"
    )
