"""Process Entity object."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ocsf._base import OCSFBaseModel


class ProcessEntity(OCSFBaseModel):
    """The Process Entity object provides critical fields for referencing a process.

    See: https://schema.ocsf.io/1.6.0/objects/process_entity
    """

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
    name: Any | None = Field(
        default=None,
        description="The friendly name of the process, for example: <code>Notepad++</code>.",
    )
    path: str | None = Field(default=None, description="The process file path.")
    pid: int | None = Field(
        default=None,
        description="The process identifier, as reported by the operating system. Process ID (PID) is a number used by the operating system to uniquely identify an active process. [Recommended]",
    )
    uid: str | None = Field(
        default=None,
        description="A unique identifier for this process assigned by the producer (tool).  Facilitates correlation of a process event with other events for that process.",
    )
