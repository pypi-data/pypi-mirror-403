"""Session object."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Session(OCSFBaseModel):
    """The Session object describes details about an authenticated session. e.g. Session Creation Time, Session Issuer. Defined by D3FEND <a target='_blank' href='https://d3fend.mitre.org/dao/artifact/d3f:Session/'>d3f:Session</a>.

    See: https://schema.ocsf.io/1.0.0/objects/session
    """

    created_time: int | None = Field(
        default=None, description="The time when the session was created. [Recommended]"
    )
    credential_uid: str | None = Field(
        default=None,
        description="The unique identifier of the user's credential. For example, AWS Access Key ID.",
    )
    expiration_time: int | None = Field(default=None, description="The session expiration time.")
    is_remote: bool | None = Field(
        default=None, description="The indication of whether the session is remote. [Recommended]"
    )
    issuer: str | None = Field(
        default=None, description="The identifier of the session issuer. [Recommended]"
    )
    uid: str | None = Field(
        default=None, description="The unique identifier of the session. [Recommended]"
    )
    uuid: Any | None = Field(
        default=None, description="The universally unique identifier of the session."
    )
