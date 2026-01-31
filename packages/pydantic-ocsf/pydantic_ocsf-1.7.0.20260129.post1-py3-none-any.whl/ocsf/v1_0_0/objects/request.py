"""Request Elements object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Request(OCSFBaseModel):
    """The Request Elements object describes characteristics of an API request.

    See: https://schema.ocsf.io/1.0.0/objects/request
    """

    uid: str = Field(..., description="The unique request identifier.")
    flags: list[str] | None = Field(
        default=None,
        description="The list of communication flags, normalized to the captions of the flag_ids values. In the case of 'Other', they are defined by the event source.",
    )
