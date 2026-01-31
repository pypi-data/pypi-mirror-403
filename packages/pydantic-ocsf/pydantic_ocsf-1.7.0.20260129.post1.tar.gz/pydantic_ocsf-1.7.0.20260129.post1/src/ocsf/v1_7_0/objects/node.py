"""Node object."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Node(OCSFBaseModel):
    """Represents a node or a vertex in a graph structure.

    See: https://schema.ocsf.io/1.7.0/objects/node
    """

    uid: str = Field(
        ...,
        description="A unique string or numeric identifier that distinguishes this node from all others in the graph. Must be unique across all nodes.",
    )
    data: dict[str, Any] | None = Field(
        default=None,
        description="Additional data about the node stored as key-value pairs. Can include custom properties specific to the node.",
    )
    desc: str | None = Field(
        default=None,
        description="A human-readable description of the node's purpose or meaning in the graph.",
    )
    name: str | None = Field(
        default=None,
        description="A human-readable name or label for the node. Should be descriptive and unique within the graph context. [Recommended]",
    )
    type_: str | None = Field(
        default=None,
        description="Categorizes the node into a specific class or type. Useful for grouping and filtering nodes.",
    )
