"""Schema Extension object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Extension(OCSFBaseModel):
    """The OCSF Schema Extension object provides detailed information about the schema extension used to construct the event. The schema extensions are registered in the <a target='_blank' href='https://github.com/ocsf/ocsf-schema/blob/main/extensions.md'>extensions.md</a> file.

    See: https://schema.ocsf.io/1.5.0/objects/extension
    """

    name: str = Field(..., description="The schema extension name. For example: <code>dev</code>.")
    uid: str = Field(
        ..., description="The schema extension unique identifier. For example: <code>999</code>."
    )
    version: str = Field(
        ..., description="The schema extension version. For example: <code>1.0.0-alpha.2</code>."
    )
