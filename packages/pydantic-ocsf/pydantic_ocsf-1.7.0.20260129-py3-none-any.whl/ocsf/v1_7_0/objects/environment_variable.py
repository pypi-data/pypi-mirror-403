"""Environment Variable object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class EnvironmentVariable(OCSFBaseModel):
    """An environment variable.

    See: https://schema.ocsf.io/1.7.0/objects/environment_variable
    """

    name: str = Field(..., description="The name of the environment variable.")
    value: str = Field(..., description="The value of the environment variable.")
