"""Affected Code object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.objects.file import File
    from ocsf.v1_6_0.objects.remediation import Remediation
    from ocsf.v1_6_0.objects.rule import Rule
    from ocsf.v1_6_0.objects.user import User


class AffectedCode(OCSFBaseModel):
    """The Affected Code object describes details about a code block identified as vulnerable.

    See: https://schema.ocsf.io/1.6.0/objects/affected_code
    """

    file: File = Field(
        ..., description="Details about the file that contains the affected code block."
    )
    end_column: int | None = Field(
        default=None,
        description="The column number of the last part of the assessed code identified as vulnerable. [Recommended]",
    )
    end_line: int | None = Field(
        default=None,
        description="The line number of the last line of code block identified as vulnerable. [Recommended]",
    )
    owner: User | None = Field(
        default=None, description="Details about the user that owns the affected file."
    )
    remediation: Remediation | None = Field(
        default=None,
        description="Describes the recommended remediation steps to address identified issue(s).",
    )
    rule: Rule | None = Field(
        default=None,
        description="Details about the specific rule, e.g., those defined as part of a larger <code>policy</code>, that triggered the finding. [Recommended]",
    )
    start_column: int | None = Field(
        default=None,
        description="The column number of the first part of the assessed code identified as vulnerable. [Recommended]",
    )
    start_line: int | None = Field(
        default=None,
        description="The line number of the first line of code block identified as vulnerable. [Recommended]",
    )
