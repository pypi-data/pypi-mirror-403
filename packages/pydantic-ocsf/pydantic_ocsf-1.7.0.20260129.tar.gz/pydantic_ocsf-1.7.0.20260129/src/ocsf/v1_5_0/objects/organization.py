"""Organization object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Organization(OCSFBaseModel):
    """The Organization object describes characteristics of an organization or company and its division if any. Additionally, it also describes cloud and Software-as-a-Service (SaaS) logical hierarchies such as AWS Organizations, Google Cloud Organizations, Oracle Cloud Tenancies, and similar constructs.

    See: https://schema.ocsf.io/1.5.0/objects/organization
    """

    name: str | None = Field(
        default=None,
        description="The name of the organization, Oracle Cloud Tenancy, Google Cloud Organization, or AWS Organization. For example, <code> Widget, Inc. </code> or the <code> AWS Organization name </code>.",
    )
    ou_name: str | None = Field(
        default=None,
        description="The name of an organizational unit, Google Cloud Folder, or AWS Org Unit. For example, the <code> GCP Project Name </code>, or <code> Dev_Prod_OU </code>. [Recommended]",
    )
    ou_uid: str | None = Field(
        default=None,
        description="The unique identifier of an organizational unit, Google Cloud Folder, or AWS Org Unit. For example, an  <code> Oracle Cloud Tenancy ID </code>, <code> AWS OU ID </code>, or <code> GCP Folder ID </code>.",
    )
    uid: str | None = Field(
        default=None,
        description="The unique identifier of the organization, Oracle Cloud Tenancy, Google Cloud Organization, or AWS Organization. For example, an <code> AWS Org ID </code> or <code> Oracle Cloud Domain ID </code>.",
    )
