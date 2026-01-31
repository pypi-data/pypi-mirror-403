"""Edge object."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Edge(OCSFBaseModel):
    """Represents a connection or relationship between two nodes in a graph.

    See: https://schema.ocsf.io/1.5.0/objects/edge
    """

    source: str = Field(
        ..., description="The unique identifier of the node where the edge originates."
    )
    target: str = Field(
        ..., description="The unique identifier of the node where the edge terminates."
    )
    data: dict[str, Any] | None = Field(
        default=None,
        description="Additional data about the edge such as weight, distance, or custom properties.",
    )
    is_directed: bool | None = Field(
        default=None,
        description="Indicates whether the edge is (<code>true</code>) or undirected (<code>false</code>).",
    )
    name: str | None = Field(
        default=None, description="The human-readable name or label for the edge. [Recommended]"
    )
    relation: str | None = Field(
        default=None,
        description="The type of relationship between nodes (e.g. is-attached-to , depends-on, etc). [Recommended]",
    )
    uid: str | None = Field(
        default=None, description="Unique identifier of the edge. [Recommended]"
    )
