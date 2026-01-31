"""Remediation object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Remediation(OCSFBaseModel):
    """The Remediation object describes details about recommended remediation strategies.

    See: https://schema.ocsf.io/1.0.0/objects/remediation
    """

    desc: str | None = Field(
        default=None, description="The description of the remediation strategy."
    )
    kb_articles: list[str] | None = Field(
        default=None, description="The KB article/s related to the entity [Recommended]"
    )
