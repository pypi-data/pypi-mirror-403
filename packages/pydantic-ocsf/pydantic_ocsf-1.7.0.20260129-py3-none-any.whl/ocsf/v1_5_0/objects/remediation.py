"""Remediation object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.objects.cis_control import CisControl
    from ocsf.v1_5_0.objects.kb_article import KbArticle


class Remediation(OCSFBaseModel):
    """The Remediation object describes the recommended remediation steps to address identified issue(s).

    See: https://schema.ocsf.io/1.5.0/objects/remediation
    """

    desc: str = Field(..., description="The description of the remediation strategy.")
    cis_controls: list[CisControl] | None = Field(
        default=None,
        description="An array of Center for Internet Security (CIS) Controls that can be optionally mapped to provide additional remediation details.",
    )
    kb_article_list: list[KbArticle] | None = Field(
        default=None,
        description="A list of KB articles or patches related to an endpoint. A KB Article contains metadata that describes the patch or an update.",
    )
    kb_articles: list[str] | None = Field(
        default=None,
        description="The KB article/s related to the entity. A KB Article contains metadata that describes the patch or an update.",
    )
    references: list[str] | None = Field(
        default=None,
        description="A list of supporting URL/s, references that help describe the remediation strategy.",
    )
