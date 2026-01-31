"""Response Elements object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Response(OCSFBaseModel):
    """The Response Elements object describes characteristics of an API response.

    See: https://schema.ocsf.io/1.0.0/objects/response
    """

    code: int | None = Field(
        default=None, description="The numeric response sent to a request. [Recommended]"
    )
    error: str | None = Field(default=None, description="Error Code [Recommended]")
    error_message: str | None = Field(default=None, description="Error Message [Recommended]")
    flags: list[str] | None = Field(
        default=None,
        description="The list of communication flags, normalized to the captions of the flag_ids values. In the case of 'Other', they are defined by the event source.",
    )
    message: str | None = Field(
        default=None,
        description="The description of the event, as defined by the event source. [Recommended]",
    )
