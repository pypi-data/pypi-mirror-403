"""Cloud object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_1_0.objects.account import Account
    from ocsf.v1_1_0.objects.organization import Organization


class Cloud(OCSFBaseModel):
    """The Cloud object contains information about a cloud account such as AWS Account ID, regions, etc.

    See: https://schema.ocsf.io/1.1.0/objects/cloud
    """

    provider: str = Field(
        ...,
        description="The unique name of the Cloud services provider, such as AWS, MS Azure, GCP, etc.",
    )
    account: Account | None = Field(
        default=None,
        description="The account object describes details about the account that was the source or target of the activity.",
    )
    org: Organization | None = Field(
        default=None, description="Organization and org unit relevant to the event or object."
    )
    project_uid: str | None = Field(
        default=None, description="The unique identifier of a Cloud project."
    )
    region: str | None = Field(
        default=None,
        description="The name of the cloud region, as defined by the cloud provider. [Recommended]",
    )
    zone: str | None = Field(
        default=None,
        description="The availability zone in the cloud region, as defined by the cloud provider.",
    )
