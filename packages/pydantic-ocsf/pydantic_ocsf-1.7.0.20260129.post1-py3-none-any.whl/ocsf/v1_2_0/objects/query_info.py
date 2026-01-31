"""Query Information object."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ocsf._base import OCSFBaseModel


class QueryInfo(OCSFBaseModel):
    """The query info object holds information related to data access within a datastore. To access, manipulate, delete, or retrieve data from a datastore, a query must be written using a specific syntax.

    See: https://schema.ocsf.io/1.2.0/objects/query_info
    """

    query_string: str = Field(
        ...,
        description="A string representing the query code being run. For example: <code>SELECT * FROM my_table</code>",
    )
    bytes: int | None = Field(
        default=None, description="The size of the data returned from the query."
    )
    data: dict[str, Any] | None = Field(
        default=None, description="The data returned from the query execution."
    )
    name: str | None = Field(
        default=None, description="The query name for a saved or scheduled query."
    )
    query_time: int | None = Field(default=None, description="The time when the query was run.")
    uid: str | None = Field(default=None, description="The unique identifier of the query.")
