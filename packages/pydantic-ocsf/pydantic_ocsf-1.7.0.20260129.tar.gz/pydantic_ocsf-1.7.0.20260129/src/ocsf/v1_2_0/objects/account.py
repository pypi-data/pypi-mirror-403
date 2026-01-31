"""Account object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_2_0.enums.type_id import TypeId


class Account(OCSFBaseModel):
    """The Account object contains details about the account that initiated or performed a specific activity within a system or application.

    See: https://schema.ocsf.io/1.2.0/objects/account
    """

    labels: list[str] | None = Field(
        default=None, description="The list of labels/tags associated to the account."
    )
    name: str | None = Field(
        default=None, description="The name of the account (e.g. GCP Account Name)."
    )
    type_: str | None = Field(
        default=None,
        description="The account type, normalized to the caption of 'account_type_id'. In the case of 'Other', it is defined by the event source.",
    )
    type_id: TypeId | None = Field(
        default=None, description="The normalized account type identifier. [Recommended]"
    )
    uid: str | None = Field(
        default=None, description="The unique identifier of the account (e.g. AWS Account ID)."
    )
