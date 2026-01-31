"""Kernel Extension object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.objects.file import File


class KernelDriver(OCSFBaseModel):
    """The Kernel Extension object describes a kernel driver that has been loaded or unloaded into the operating system (OS) kernel.

    See: https://schema.ocsf.io/1.5.0/objects/kernel_driver
    """

    file: File = Field(..., description="The driver/extension file object.")
