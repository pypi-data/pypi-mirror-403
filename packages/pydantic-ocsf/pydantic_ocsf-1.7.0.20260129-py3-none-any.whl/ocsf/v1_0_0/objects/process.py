"""Process object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_0_0.enums.integrity_id import IntegrityId
    from ocsf.v1_0_0.objects.file import File
    from ocsf.v1_0_0.objects.object import Object
    from ocsf.v1_0_0.objects.session import Session
    from ocsf.v1_0_0.objects.user import User


class Process(OCSFBaseModel):
    """The Process object describes a running instance of a launched program. Defined by D3FEND <a target='_blank' href='https://d3fend.mitre.org/dao/artifact/d3f:Process/'>d3f:Process</a>.

    See: https://schema.ocsf.io/1.0.0/objects/process
    """

    cmd_line: str | None = Field(
        default=None,
        description="The full command line used to launch an application, service, process, or job. For example: <code>ssh user@10.0.0.10</code>. If the command line is unavailable or missing, the empty string <code>''</code> is to be used [Recommended]",
    )
    created_time: int | None = Field(
        default=None, description="The time when the process was created/started. [Recommended]"
    )
    file: File | None = Field(default=None, description="The process file object. [Recommended]")
    include: str | None = Field(default=None, description="")
    integrity: str | None = Field(
        default=None,
        description="The process integrity level, normalized to the caption of the direction_id value. In the case of 'Other', it is defined by the event source (Windows only).",
    )
    integrity_id: IntegrityId | None = Field(
        default=None,
        description="The normalized identifier of the process integrity level (Windows only).",
    )
    lineage: list[str] | None = Field(
        default=None,
        description="The lineage of the process, represented by a list of paths for each ancestor process. For example: <code>['/usr/sbin/sshd', '/usr/bin/bash', '/usr/bin/whoami']</code>",
    )
    loaded_modules: list[str] | None = Field(
        default=None, description="The list of loaded module names."
    )
    name: Any | None = Field(
        default=None,
        description="The friendly name of the process, for example: <code>Notepad++</code>.",
    )
    parent_process: Process | None = Field(
        default=None,
        description="The parent process of this process object. It is recommended to only populate this field for the first process object, to prevent deep nesting. [Recommended]",
    )
    pid: int | None = Field(
        default=None,
        description="The process identifier, as reported by the operating system. Process ID (PID) is a number used by the operating system to uniquely identify an active process. [Recommended]",
    )
    sandbox: str | None = Field(
        default=None,
        description="The name of the containment jail (i.e., sandbox). For example, hardened_ps, high_security_ps, oracle_ps, netsvcs_ps, or default_ps.",
    )
    session: Session | None = Field(
        default=None, description="The user session under which this process is running."
    )
    terminated_time: int | None = Field(
        default=None, description="The time when the process was terminated."
    )
    tid: int | None = Field(
        default=None,
        description="The Identifier of the thread associated with the event, as returned by the operating system.",
    )
    uid: str | None = Field(
        default=None,
        description="A unique identifier for this process assigned by the producer (tool).  Facilitates correlation of a process event with other events for that process.",
    )
    user: User | None = Field(
        default=None, description="The user under which this process is running. [Recommended]"
    )
    xattributes: Object | None = Field(
        default=None,
        description="An unordered collection of zero or more name/value pairs that represent a process extended attribute.",
    )
