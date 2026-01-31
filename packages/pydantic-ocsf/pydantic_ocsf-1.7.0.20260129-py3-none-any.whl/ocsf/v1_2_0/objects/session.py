"""Session object."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Session(OCSFBaseModel):
    """The Session object describes details about an authenticated session. e.g. Session Creation Time, Session Issuer. Defined by D3FEND <a target='_blank' href='https://d3fend.mitre.org/dao/artifact/d3f:Session/'>d3f:Session</a>.

    See: https://schema.ocsf.io/1.2.0/objects/session
    """

    count: int | None = Field(
        default=None,
        description="The number of identical sessions spawned from the same source IP, destination IP, application, and content/threat type seen over a period of time.",
    )
    created_time: int | None = Field(
        default=None, description="The time when the session was created. [Recommended]"
    )
    credential_uid: str | None = Field(
        default=None,
        description="The unique identifier of the user's credential. For example, AWS Access Key ID.",
    )
    expiration_reason: str | None = Field(
        default=None, description="The reason which triggered the session expiration."
    )
    expiration_time: int | None = Field(default=None, description="The session expiration time.")
    is_mfa: bool | None = Field(
        default=None,
        description="Indicates whether Multi Factor Authentication was used during authentication.",
    )
    is_remote: bool | None = Field(
        default=None, description="The indication of whether the session is remote. [Recommended]"
    )
    is_vpn: bool | None = Field(
        default=None, description="The indication of whether the session is a VPN session."
    )
    issuer: str | None = Field(
        default=None, description="The identifier of the session issuer. [Recommended]"
    )
    terminal: str | None = Field(
        default=None,
        description="The Pseudo Terminal associated with the session. Ex: the tty or pts value.",
    )
    uid: str | None = Field(
        default=None, description="The unique identifier of the session. [Recommended]"
    )
    uid_alt: str | None = Field(
        default=None,
        description="The alternate unique identifier of the session. e.g. AWS ARN - <code>arn:aws:sts::123344444444:assumed-role/Admin/example-session</code>.",
    )
    uuid: Any | None = Field(
        default=None, description="The universally unique identifier of the session."
    )
