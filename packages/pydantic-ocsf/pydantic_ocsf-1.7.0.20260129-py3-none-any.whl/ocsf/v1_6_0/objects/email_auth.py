"""Email Authentication object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class EmailAuth(OCSFBaseModel):
    """The Email Authentication object describes the Sender Policy Framework (SPF), DomainKeys Identified Mail (DKIM) and Domain-based Message Authentication, Reporting and Conformance (DMARC) attributes of an email.

    See: https://schema.ocsf.io/1.6.0/objects/email_auth
    """

    dkim: str | None = Field(
        default=None,
        description="The DomainKeys Identified Mail (DKIM) status of the email. [Recommended]",
    )
    dkim_domain: str | None = Field(
        default=None,
        description="The DomainKeys Identified Mail (DKIM) signing domain of the email. [Recommended]",
    )
    dkim_signature: str | None = Field(
        default=None,
        description="The DomainKeys Identified Mail (DKIM) signature used by the sending/receiving system. [Recommended]",
    )
    dmarc: str | None = Field(
        default=None,
        description="The Domain-based Message Authentication, Reporting and Conformance (DMARC) status of the email. [Recommended]",
    )
    dmarc_override: str | None = Field(
        default=None,
        description="The Domain-based Message Authentication, Reporting and Conformance (DMARC) override action. [Recommended]",
    )
    dmarc_policy: str | None = Field(
        default=None,
        description="The Domain-based Message Authentication, Reporting and Conformance (DMARC) policy status. [Recommended]",
    )
    spf: str | None = Field(
        default=None,
        description="The Sender Policy Framework (SPF) status of the email. [Recommended]",
    )
