"""Database object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.enums.type_id import TypeId
    from ocsf.v1_6_0.objects.group import Group


class Database(OCSFBaseModel):
    """The database object is used for databases which are typically datastore services that contain an organized collection of structured and unstructured data or a types of data.

    See: https://schema.ocsf.io/1.6.0/objects/database
    """

    type_id: TypeId = Field(..., description="The normalized identifier of the database type.")
    created_time: int | None = Field(
        default=None, description="The time when the database was known to have been created."
    )
    desc: str | None = Field(default=None, description="The description of the database.")
    groups: list[Group] | None = Field(
        default=None, description="The group names to which the database belongs."
    )
    include: str | None = Field(default=None, description="")
    modified_time: int | None = Field(
        default=None,
        description="The most recent time when any changes, updates, or modifications were made within the database.",
    )
    name: str | None = Field(
        default=None,
        description="The database name, ordinarily as assigned by a database administrator.",
    )
    size: int | None = Field(default=None, description="The size of the database in bytes.")
    type_: str | None = Field(default=None, description="The database type. [Recommended]")
    uid: str | None = Field(default=None, description="The unique identifier of the database.")
