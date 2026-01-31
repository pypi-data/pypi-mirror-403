"""Startup Item object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.enums.run_mode_ids import RunModeIds
    from ocsf.v1_7_0.enums.run_state_id import RunStateId
    from ocsf.v1_7_0.enums.start_type_id import StartTypeId
    from ocsf.v1_7_0.enums.type_id import TypeId
    from ocsf.v1_7_0.objects.job import Job
    from ocsf.v1_7_0.objects.kernel_driver import KernelDriver
    from ocsf.v1_7_0.objects.process import Process


class StartupItem(OCSFBaseModel):
    """The startup item object describes an application component that has associated startup criteria and configurations.

    See: https://schema.ocsf.io/1.7.0/objects/startup_item
    """

    name: str = Field(..., description="The unique name of the startup item.")
    start_type_id: StartTypeId = Field(..., description="The start type ID of the startup item.")
    driver: KernelDriver | None = Field(
        default=None, description="The startup item kernel driver resource."
    )
    job: Job | None = Field(default=None, description="The startup item job resource.")
    process: Process | None = Field(default=None, description="The startup item process resource.")
    run_mode_ids: list[RunModeIds] | None = Field(
        default=None,
        description="The list of normalized identifiers that describe the startup items' properties when it is running.  Use this field to capture extended information about the process, which may depend on the type of startup item.  E.g., A Windows service that interacts with the desktop.",
    )
    run_modes: list[str] | None = Field(
        default=None,
        description="The list of run_modes, normalized to the captions of the run_mode_id values.  In the case of 'Other', they are defined by the event source.",
    )
    run_state: str | None = Field(default=None, description="The run state of the startup item.")
    run_state_id: RunStateId | None = Field(
        default=None, description="The run state ID of the startup item. [Recommended]"
    )
    start_type: str | None = Field(default=None, description="The start type of the startup item.")
    type_: str | None = Field(default=None, description="The startup item type.")
    type_id: TypeId | None = Field(
        default=None, description="The startup item type identifier. [Recommended]"
    )
