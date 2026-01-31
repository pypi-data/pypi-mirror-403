"""Long String object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class LongString(OCSFBaseModel):
    """This object is a used to capture strings which may be truncated by a security product due to their length.

    See: https://schema.ocsf.io/1.5.0/objects/long_string
    """

    value: str = Field(
        ...,
        description="The string value, truncated if <code>is_truncated</code> is <code>true</code>.",
    )
    is_truncated: bool | None = Field(
        default=None,
        description="Indicates that <code>value</code> has been truncated. May be omitted if truncation has not occurred.",
    )
    untruncated_size: int | None = Field(
        default=None,
        description="The size in bytes of the string represented by <code>value</code> before truncation. Should be omitted if truncation has not occurred.",
    )
