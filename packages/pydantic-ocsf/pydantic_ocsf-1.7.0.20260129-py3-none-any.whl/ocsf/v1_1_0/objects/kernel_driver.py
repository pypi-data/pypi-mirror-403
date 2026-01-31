"""Kernel Extension object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_1_0.objects.file import File


class KernelDriver(OCSFBaseModel):
    """The Kernel Extension object describes a kernel driver that has been loaded or unloaded into the operating system (OS) kernel. Defined by D3FEND <a target='_blank' href='https://d3fend.mitre.org/dao/artifact/d3f:KernelModule/'>d3f:KernelModule</a>.

    See: https://schema.ocsf.io/1.1.0/objects/kernel_driver
    """

    file: File = Field(..., description="The driver/extension file object.")
