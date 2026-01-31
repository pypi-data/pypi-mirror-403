"""Parameter object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Parameter(OCSFBaseModel):
    """The Parameter object provides details regarding a parameter of a a function.

    See: https://schema.ocsf.io/1.7.0/objects/parameter
    """

    name: str | None = Field(default=None, description="The parameter name.")
    post_value: str | None = Field(
        default=None, description="The parameter value after function execution."
    )
    pre_value: str | None = Field(
        default=None, description="The parameter value before function execution."
    )
