"""Script object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.type_id import TypeId
    from ocsf.v1_5_0.objects.file import File
    from ocsf.v1_5_0.objects.fingerprint import Fingerprint
    from ocsf.v1_5_0.objects.long_string import LongString


class Script(OCSFBaseModel):
    """The Script object describes a script or command that can be executed by a shell, script engine, or interpreter. Examples include Bash, JavsScript, PowerShell, Python, VBScript, etc. Note that the term <em>script</em> here denotes not only a script contained within a file but also a script or command typed interactively by a user, supplied on the command line, or provided by some other file-less mechanism.

    See: https://schema.ocsf.io/1.5.0/objects/script
    """

    script_content: LongString = Field(
        ...,
        description="The script content, normalized to UTF-8 encoding irrespective of its original encoding. When emitting this attribute, it may be appropriate to truncate large scripts. When consuming this attribute, large scripts should be anticipated.",
    )
    type_id: TypeId = Field(..., description="The normalized script type ID.")
    file: File | None = Field(
        default=None,
        description="Present if this script is associated with a file. Not present in the case of a file-less script.",
    )
    hashes: list[Fingerprint] | None = Field(
        default=None,
        description="An array of the script's cryptographic hashes. Note that these hashes are calculated on the script in its original encoding, and not on the normalized UTF-8 encoding found in the <code>script_content</code> attribute. [Recommended]",
    )
    name: str | None = Field(
        default=None,
        description="Unique identifier for the script or macro, independent of the containing file, used for tracking, auditing, and security analysis.",
    )
    parent_uid: str | None = Field(
        default=None,
        description="This attribute relates a sub-script to a parent script having the matching <code>uid</code> attribute. In the case of PowerShell, sub-script execution can be identified by matching the activity correlation ID of the raw ETW events provided by the OS.",
    )
    type_: str | None = Field(
        default=None,
        description="The script type, normalized to the caption of the <code>type_id</code> value. In the case of 'Other', it is defined by the event source.",
    )
    uid: str | None = Field(
        default=None,
        description="Some script engines assign a unique ID to each individual execution of a given script. This attribute captures that unique ID. In the case of PowerShell, the unique ID corresponds to the <code>ScriptBlockId</code> in the raw ETW events provided by the OS.",
    )
