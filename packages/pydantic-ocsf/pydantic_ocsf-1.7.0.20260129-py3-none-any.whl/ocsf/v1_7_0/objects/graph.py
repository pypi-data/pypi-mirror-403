"""Graph object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.enums.query_language_id import QueryLanguageId
    from ocsf.v1_7_0.objects.edge import Edge
    from ocsf.v1_7_0.objects.node import Node


class Graph(OCSFBaseModel):
    """A graph data structure representation with nodes and edges.

    See: https://schema.ocsf.io/1.7.0/objects/graph
    """

    nodes: list[Node] = Field(
        ...,
        description="The nodes/vertices of the graph - contains the collection of <code>node</code> objects that make up the graph.",
    )
    desc: str | None = Field(
        default=None,
        description="The graph description - provides additional details about the graph's purpose and contents.",
    )
    edges: list[Edge] | None = Field(
        default=None,
        description="The edges/connections between nodes in the graph - contains the collection of <code>edge</code> objects defining relationships between nodes.",
    )
    is_directed: bool | None = Field(
        default=None,
        description="Indicates if the graph is directed (<code>true</code>) or undirected (<code>false</code>).",
    )
    name: str | None = Field(
        default=None, description="The graph name - a human readable identifier for the graph."
    )
    query_language: str | None = Field(
        default=None,
        description="The graph query language, normalized to the caption of the <code>query_language_id</code> value.",
    )
    query_language_id: QueryLanguageId | None = Field(
        default=None,
        description="The normalized identifier of a graph query language that can be used to interact with the graph. [Recommended]",
    )
    type_: str | None = Field(
        default=None,
        description="The graph type. Typically useful to represent the specific type of graph that is used.",
    )
    uid: str | None = Field(
        default=None,
        description="Unique identifier of the graph - a unique ID to reference this specific graph.",
    )
