"""Managed Entity object."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ocsf._base import OCSFBaseModel


class ManagedEntity(OCSFBaseModel):
    """The Managed Entity object describes the type and version of an entity, such as a policy or configuration.

    See: https://schema.ocsf.io/1.2.0/objects/managed_entity
    """

    data: dict[str, Any] | None = Field(
        default=None, description="The managed entity content as a JSON object."
    )
    name: str | None = Field(default=None, description="The name of the managed entity.")
    type_: str | None = Field(
        default=None,
        description="The managed entity type. For example: <code>policy</code>, <code>user</code>, <code>organizational unit</code>, <code>device</code>. [Recommended]",
    )
    uid: str | None = Field(default=None, description="The identifier of the managed entity.")
    version: str | None = Field(
        default=None,
        description="The version of the managed entity. For example: <code>1.2.3</code>. [Recommended]",
    )
