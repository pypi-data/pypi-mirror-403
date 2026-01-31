"""Function Invocation object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.objects.parameter import Parameter


class FunctionInvocation(OCSFBaseModel):
    """The Function Invocation object provides details regarding the invocation of a function.

    See: https://schema.ocsf.io/1.7.0/objects/function_invocation
    """

    error: str | None = Field(
        default=None,
        description="The error indication returned from the function. This may differ from the return value (e.g. when <code>errno</code> is used).",
    )
    parameters: list[Parameter] | None = Field(
        default=None, description="The parameters passed into a function invocation."
    )
    return_value: str | None = Field(
        default=None, description="The value returned from a function."
    )
