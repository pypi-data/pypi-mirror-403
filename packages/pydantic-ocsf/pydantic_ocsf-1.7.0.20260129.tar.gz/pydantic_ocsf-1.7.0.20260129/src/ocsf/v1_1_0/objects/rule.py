"""Rule object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Rule(OCSFBaseModel):
    """The Rule object describes characteristics of a rule associated with a policy or an event.

    See: https://schema.ocsf.io/1.1.0/objects/rule
    """

    category: str | None = Field(default=None, description="The rule category.")
    desc: str | None = Field(
        default=None, description="The description of the rule that generated the event."
    )
    name: str | None = Field(
        default=None, description="The name of the rule that generated the event."
    )
    type_: str | None = Field(default=None, description="The rule type.")
    uid: str | None = Field(
        default=None, description="The unique identifier of the rule that generated the event."
    )
    version: str | None = Field(
        default=None, description="The rule version. For example: <code>1.1</code>."
    )
