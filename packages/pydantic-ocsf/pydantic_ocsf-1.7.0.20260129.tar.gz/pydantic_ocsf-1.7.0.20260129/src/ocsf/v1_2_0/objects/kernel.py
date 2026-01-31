"""Kernel Resource object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_2_0.enums.type_id import TypeId


class Kernel(OCSFBaseModel):
    """The Kernel Resource object provides information about a specific kernel resource, including its name and type. It describes essential attributes associated with a resource managed by the kernel of an operating system. Defined by D3FEND <a target='_blank' href='https://d3fend.mitre.org/dao/artifact/d3f:Kernel/'>d3f:Kernel</a>.

    See: https://schema.ocsf.io/1.2.0/objects/kernel
    """

    name: str = Field(..., description="The name of the kernel resource.")
    type_id: TypeId = Field(..., description="The type of the kernel resource.")
    is_system: bool | None = Field(
        default=None,
        description="The indication of whether the object is part of the operating system.",
    )
    path: str | None = Field(default=None, description="The full path of the kernel resource.")
    system_call: str | None = Field(default=None, description="The system call that was invoked.")
    type_: str | None = Field(default=None, description="The type of the kernel resource.")
