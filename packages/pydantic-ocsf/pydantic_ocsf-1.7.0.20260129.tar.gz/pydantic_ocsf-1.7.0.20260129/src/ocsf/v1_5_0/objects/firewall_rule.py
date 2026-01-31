"""Firewall Rule object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class FirewallRule(OCSFBaseModel):
    """The Firewall Rule object represents a specific rule within a firewall policy or event. It contains information about a rule's configuration, properties, and associated actions that define how network traffic is handled by the firewall.

    See: https://schema.ocsf.io/1.5.0/objects/firewall_rule
    """

    category: str | None = Field(default=None, description="The rule category.")
    condition: str | None = Field(
        default=None,
        description="The rule trigger condition for the rule. For example: SQL_INJECTION.",
    )
    desc: str | None = Field(
        default=None, description="The description of the rule that generated the event."
    )
    duration: int | None = Field(
        default=None,
        description="The rule response time duration, usually used for challenge completion time.",
    )
    match_details: list[str] | None = Field(
        default=None,
        description='The data in a request that rule matched. For example: \'["10","and","1"]\'.',
    )
    match_location: str | None = Field(
        default=None,
        description="The location of the matched data in the source which resulted in the triggered firewall rule. For example: HEADER.",
    )
    name: str | None = Field(
        default=None, description="The name of the rule that generated the event."
    )
    rate_limit: int | None = Field(
        default=None, description="The rate limit for a rate-based rule."
    )
    sensitivity: str | None = Field(
        default=None,
        description="The sensitivity of the firewall rule in the matched event. For example: HIGH.",
    )
    type_: str | None = Field(default=None, description="The rule type.")
    uid: str | None = Field(
        default=None, description="The unique identifier of the rule that generated the event."
    )
    version: str | None = Field(
        default=None, description="The rule version. For example: <code>1.1</code>."
    )
