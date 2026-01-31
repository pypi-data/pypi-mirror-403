"""Email object."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Email(OCSFBaseModel):
    """The Email object describes the email metadata such as sender, recipients, and direction. Defined by D3FEND <a target='_blank' href='https://d3fend.mitre.org/dao/artifact/d3f:Email/'>d3f:Email</a>.

    See: https://schema.ocsf.io/1.1.0/objects/email
    """

    from_: Any = Field(..., description="The email header From values, as defined by RFC 5322.")
    to: list[Any] = Field(..., description="The email header To values, as defined by RFC 5322.")
    cc: list[Any] | None = Field(
        default=None, description="The email header Cc values, as defined by RFC 5322."
    )
    delivered_to: Any | None = Field(
        default=None, description="The <strong>Delivered-To</strong> email header field."
    )
    message_uid: str | None = Field(
        default=None,
        description="The email header Message-Id value, as defined by RFC 5322. [Recommended]",
    )
    raw_header: str | None = Field(default=None, description="The email authentication header.")
    reply_to: Any | None = Field(
        default=None,
        description="The email header Reply-To values, as defined by RFC 5322. [Recommended]",
    )
    size: int | None = Field(
        default=None,
        description="The size in bytes of the email, including attachments. [Recommended]",
    )
    smtp_from: Any | None = Field(
        default=None, description="The value of the SMTP MAIL FROM command. [Recommended]"
    )
    smtp_to: list[Any] | None = Field(
        default=None, description="The value of the SMTP envelope RCPT TO command. [Recommended]"
    )
    subject: str | None = Field(
        default=None, description="The email header Subject value, as defined by RFC 5322."
    )
    uid: str | None = Field(default=None, description="The email unique identifier. [Recommended]")
    x_originating_ip: list[Any] | None = Field(
        default=None,
        description="The X-Originating-IP header identifying the emails originating IP address(es).",
    )
