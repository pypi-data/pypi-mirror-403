"""Table object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.objects.group import Group


class Table(OCSFBaseModel):
    """The table object represents a table within a structured relational database or datastore, which contains columns and rows of data that are able to be create, updated, deleted and queried.

    See: https://schema.ocsf.io/1.6.0/objects/table
    """

    created_time: int | None = Field(
        default=None, description="The time when the table was known to have been created."
    )
    desc: str | None = Field(default=None, description="The description of the table.")
    groups: list[Group] | None = Field(
        default=None, description="The group names to which the table belongs."
    )
    modified_time: int | None = Field(
        default=None,
        description="The most recent time when any changes, updates, or modifications were made within the table.",
    )
    name: str | None = Field(
        default=None,
        description="The table name, ordinarily as assigned by a database administrator.",
    )
    size: int | None = Field(default=None, description="The size of the data table in bytes.")
    uid: str | None = Field(default=None, description="The unique identifier of the table.")
