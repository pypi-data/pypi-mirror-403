"""Email object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.objects.file import File
    from ocsf.v1_6_0.objects.http_header import HttpHeader
    from ocsf.v1_6_0.objects.url import Url


class Email(OCSFBaseModel):
    """The Email object describes the email metadata such as sender, recipients, and direction, and can include embedded URLs and files.

    See: https://schema.ocsf.io/1.6.0/objects/email
    """

    cc: list[Any] | None = Field(
        default=None,
        description="The machine-readable email header Cc values, as defined by RFC 5322. For example <code>example.user@usersdomain.com</code>.",
    )
    cc_mailboxes: list[str] | None = Field(
        default=None,
        description="The human-readable email header Cc Mailbox values. For example <code>'Example User &lt;example.user@usersdomain.com&gt;'</code>.",
    )
    delivered_to: Any | None = Field(
        default=None,
        description="The machine-readable <strong>Delivered-To</strong> email header field. For example <code>example.user@usersdomain.com</code>",
    )
    delivered_to_list: list[Any] | None = Field(
        default=None,
        description="The machine-readable <strong>Delivered-To</strong> email header values. For example <code>example.user@usersdomain.com</code>",
    )
    files: list[File] | None = Field(
        default=None, description="The files embedded or attached to the email."
    )
    from_: Any | None = Field(
        default=None,
        description="The machine-readable email header From value, as defined by RFC 5322. For example <code>example.user@usersdomain.com</code>. [Recommended]",
    )
    from_list: list[Any] | None = Field(
        default=None,
        description="The machine-readable email header From values. This array should contain the value in <code>from</code>. For example <code>example.user@usersdomain.com</code>.",
    )
    from_mailbox: str | None = Field(
        default=None,
        description="The human-readable email header From Mailbox value. For example <code>'Example User &lt;example.user@usersdomain.com&gt;'</code>.",
    )
    from_mailboxes: list[Any] | None = Field(
        default=None,
        description="The human-readable email header From Mailbox values. This array should contain the value in <code>from_mailbox</code>. For example <code>'Example User &lt;example.user@usersdomain.com&gt;'</code>.",
    )
    http_headers: list[HttpHeader] | None = Field(
        default=None, description="Additional HTTP headers of an HTTP request or response."
    )
    include: str | None = Field(default=None, description="")
    is_read: bool | None = Field(
        default=None, description="The indication of whether the email has been read."
    )
    message_uid: str | None = Field(
        default=None,
        description="The email header Message-ID value, as defined by RFC 5322. [Recommended]",
    )
    raw_header: str | None = Field(default=None, description="The email authentication header.")
    reply_to: Any | None = Field(
        default=None,
        description="The machine-readable email header Reply-To value, as defined by RFC 5322. For example <code>example.user@usersdomain.com</code> [Recommended]",
    )
    reply_to_list: list[Any] | None = Field(
        default=None,
        description="The machine-readable email header Reply-To values, as defined by RFC 5322. For example <code>example.user@usersdomain.com</code>",
    )
    reply_to_mailboxes: list[str] | None = Field(
        default=None,
        description="The human-readable email header Reply To Mailbox values. For example <code>'Example User &lt;example.user@usersdomain.com&gt;'</code>.",
    )
    return_path: Any | None = Field(
        default=None,
        description="The address found in the 'Return-Path' header, which indicates where bounce messages (non-delivery reports) should be sent. This address is often set by the sending system and may differ from the 'From' or 'Sender' addresses. For example, <code>mailer-daemon@senderserver.com</code>.",
    )
    sender: Any | None = Field(
        default=None,
        description="The machine readable email address of the system or server that actually transmitted the email message, extracted from the email headers per RFC 5322. This differs from the <code>from</code> field, which shows the message author. The sender field is most commonly used when multiple addresses appear in the <code> from_list </code> field, or when the transmitting system is different from the message author (such as when sending on behalf of someone else).",
    )
    sender_mailbox: str | None = Field(
        default=None,
        description="The human readable email address of the system or server that actually transmitted the email message, extracted from the email headers per RFC 5322. This differs from the <code>from_mailbox</code> field, which shows the message author. The sender mailbox field is most commonly used when multiple addresses appear in the <code> from_mailboxes </code> field, or when the transmitting system is different from the message author (such as when sending on behalf of someone else).",
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
        default=None,
        description="The email header Subject value, as defined by RFC 5322. [Recommended]",
    )
    to: list[Any] | None = Field(
        default=None,
        description="The machine-readable email header To values, as defined by RFC 5322. For example <code>example.user@usersdomain.com</code> [Recommended]",
    )
    to_mailboxes: list[str] | None = Field(
        default=None,
        description="The human-readable email header To Mailbox values. For example <code>'Example User &lt;example.user@usersdomain.com&gt;'</code>.",
    )
    uid: str | None = Field(
        default=None, description="The unique identifier of the email thread. [Recommended]"
    )
    urls: list[Url] | None = Field(default=None, description="The URLs embedded in the email.")
    x_originating_ip: list[Any] | None = Field(
        default=None,
        description="The X-Originating-IP header identifying the emails originating IP address(es).",
    )
