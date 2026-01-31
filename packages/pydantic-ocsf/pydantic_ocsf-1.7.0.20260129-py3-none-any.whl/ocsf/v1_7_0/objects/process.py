"""Process object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.enums.integrity_id import IntegrityId
    from ocsf.v1_7_0.objects.environment_variable import EnvironmentVariable
    from ocsf.v1_7_0.objects.file import File
    from ocsf.v1_7_0.objects.object import Object
    from ocsf.v1_7_0.objects.process_entity import ProcessEntity
    from ocsf.v1_7_0.objects.session import Session
    from ocsf.v1_7_0.objects.user import User


class Process(OCSFBaseModel):
    """The Process object describes a running instance of a launched program.

    See: https://schema.ocsf.io/1.7.0/objects/process
    """

    ancestry: list[ProcessEntity] | None = Field(
        default=None,
        description="An array of Process Entities describing the extended parentage of this process object. Direct parent information should be expressed through the <code>parent_process</code> attribute. The first array element is the direct parent of this process object. Subsequent list elements go up the process parentage hierarchy. That is, the array is sorted from newest to oldest process. It is recommended to only populate this field for the top-level process object.",
    )
    cmd_line: str | None = Field(
        default=None,
        description="The full command line used to launch an application, service, process, or job. For example: <code>ssh user@10.0.0.10</code>. If the command line is unavailable or missing, the empty string <code>''</code> is to be used. [Recommended]",
    )
    cpid: Any | None = Field(
        default=None,
        description="A unique process identifier that can be assigned deterministically by multiple system data producers. [Recommended]",
    )
    created_time: int | None = Field(
        default=None, description="The time when the process was created/started. [Recommended]"
    )
    environment_variables: list[EnvironmentVariable] | None = Field(
        default=None, description="Environment variables associated with the process."
    )
    file: File | None = Field(default=None, description="The process file object. [Recommended]")
    include: str | None = Field(default=None, description="")
    integrity: str | None = Field(
        default=None,
        description="The process integrity level, normalized to the caption of the integrity_id value. In the case of 'Other', it is defined by the event source (Windows only).",
    )
    integrity_id: IntegrityId | None = Field(
        default=None,
        description="The normalized identifier of the process integrity level (Windows only).",
    )
    lineage: list[Any] | None = Field(
        default=None,
        description="The lineage of the process, represented by a list of paths for each ancestor process. For example: <code>['/usr/sbin/sshd', '/usr/bin/bash', '/usr/bin/whoami']</code>.",
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
        description="The parent process of this process object. It is recommended to only populate this field for the top-level process object, to prevent deep nesting. Additional ancestry information can be supplied in the <code>ancestry</code> attribute. [Recommended]",
    )
    path: str | None = Field(default=None, description="The process file path.")
    pid: int | None = Field(
        default=None,
        description="The process identifier, as reported by the operating system. Process ID (PID) is a number used by the operating system to uniquely identify an active process. [Recommended]",
    )
    ptid: int | None = Field(
        default=None,
        description="The identifier of the process thread associated with the event, as returned by the operating system.",
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
        description="The identifier of the thread associated with the event, as returned by the operating system.",
    )
    uid: str | None = Field(
        default=None,
        description="A unique identifier for this process assigned by the producer (tool).  Facilitates correlation of a process event with other events for that process.",
    )
    user: User | None = Field(
        default=None, description="The user under which this process is running. [Recommended]"
    )
    working_directory: str | None = Field(
        default=None, description="The working directory of a process."
    )
    xattributes: Object | None = Field(
        default=None,
        description="An unordered collection of zero or more name/value pairs that represent a process extended attribute.",
    )
