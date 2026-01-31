"""Databucket object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_2_0.enums.type_id import TypeId
    from ocsf.v1_2_0.objects.file import File
    from ocsf.v1_2_0.objects.group import Group


class Databucket(OCSFBaseModel):
    """The databucket object is a basic container that holds data, typically organized through the use of data partitions.

    See: https://schema.ocsf.io/1.2.0/objects/databucket
    """

    type_id: TypeId = Field(..., description="The normalized identifier of the databucket type.")
    created_time: int | None = Field(
        default=None, description="The time when the databucket was known to have been created."
    )
    desc: str | None = Field(default=None, description="The description of the databucket.")
    file: File | None = Field(default=None, description="A file within a databucket.")
    groups: list[Group] | None = Field(
        default=None, description="The group names to which the databucket belongs."
    )
    include: str | None = Field(default=None, description="")
    modified_time: int | None = Field(
        default=None,
        description="The most recent time when any changes, updates, or modifications were made within the databucket.",
    )
    name: str | None = Field(default=None, description="The databucket name.")
    size: int | None = Field(default=None, description="The size of the databucket in bytes.")
    type_: str | None = Field(default=None, description="The databucket type. [Recommended]")
    uid: str | None = Field(default=None, description="The unique identifier of the databucket.")
