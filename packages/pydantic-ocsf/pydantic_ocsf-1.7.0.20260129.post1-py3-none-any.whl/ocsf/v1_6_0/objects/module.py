"""Module object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.enums.load_type_id import LoadTypeId
    from ocsf.v1_6_0.objects.file import File


class Module(OCSFBaseModel):
    """The Module object describes the load attributes of a module.

    See: https://schema.ocsf.io/1.6.0/objects/module
    """

    load_type_id: LoadTypeId = Field(
        ..., description="The normalized identifier for how the module was loaded in memory."
    )
    base_address: str | None = Field(
        default=None, description="The memory address where the module was loaded. [Recommended]"
    )
    file: File | None = Field(default=None, description="The module file object. [Recommended]")
    function_name: str | None = Field(
        default=None,
        description="The entry-point function of the module. The system calls the entry-point function whenever a process or thread loads or unloads the module.",
    )
    load_type: str | None = Field(
        default=None,
        description="The load type, normalized to the caption of the load_type_id value. In the case of 'Other', it is defined by the event source.",
    )
    start_address: str | None = Field(
        default=None, description="The start address of the execution. [Recommended]"
    )
    type_: str | None = Field(default=None, description="The module type. [Recommended]")
