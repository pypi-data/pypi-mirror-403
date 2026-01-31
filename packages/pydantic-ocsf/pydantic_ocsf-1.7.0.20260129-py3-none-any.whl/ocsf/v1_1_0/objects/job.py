"""Job object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_1_0.enums.run_state_id import RunStateId
    from ocsf.v1_1_0.objects.file import File
    from ocsf.v1_1_0.objects.user import User


class Job(OCSFBaseModel):
    """The Job object provides information about a scheduled job or task, including its name, command line, and state. It encompasses attributes that describe the properties and status of the scheduled job.

    See: https://schema.ocsf.io/1.1.0/objects/job
    """

    file: File = Field(..., description="The file that pertains to the job.")
    name: str = Field(..., description="The name of the job.")
    cmd_line: str | None = Field(default=None, description="The job command line. [Recommended]")
    created_time: int | None = Field(
        default=None, description="The time when the job was created. [Recommended]"
    )
    desc: str | None = Field(default=None, description="The description of the job. [Recommended]")
    last_run_time: int | None = Field(
        default=None, description="The time when the job was last run. [Recommended]"
    )
    next_run_time: int | None = Field(
        default=None, description="The time when the job will next be run."
    )
    run_state: str | None = Field(default=None, description="The run state of the job.")
    run_state_id: RunStateId | None = Field(
        default=None, description="The run state ID of the job. [Recommended]"
    )
    user: User | None = Field(default=None, description="The user that created the job.")
