"""Account object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.enums.type_id import TypeId
    from ocsf.v1_7_0.objects.key_value_object import KeyValueObject


class Account(OCSFBaseModel):
    """The Account object contains details about the account that initiated or performed a specific activity within a system or application. Additionally, the Account object refers to logical Cloud and Software-as-a-Service (SaaS) based containers such as AWS Accounts, Azure Subscriptions, Oracle Cloud Compartments, Google Cloud Projects, and otherwise.

    See: https://schema.ocsf.io/1.7.0/objects/account
    """

    labels: list[str] | None = Field(
        default=None, description="The list of labels associated to the account."
    )
    name: str | None = Field(
        default=None,
        description="The name of the account (e.g. <code> GCP Project name </code>, <code> Linux Account name </code> or <code> AWS Account name</code>).",
    )
    tags: list[KeyValueObject] | None = Field(
        default=None,
        description="The list of tags; <code>{key:value}</code> pairs associated to the account.",
    )
    type_: str | None = Field(
        default=None,
        description="The account type, normalized to the caption of 'account_type_id'. In the case of 'Other', it is defined by the event source.",
    )
    type_id: TypeId | None = Field(
        default=None, description="The normalized account type identifier. [Recommended]"
    )
    uid: str | None = Field(
        default=None,
        description="The unique identifier of the account (e.g. <code> AWS Account ID </code>, <code> OCID </code>, <code> GCP Project ID </code>, <code> Azure Subscription ID </code>, <code> Google Workspace Customer ID </code>, or <code> M365 Tenant UID</code>).",
    )
