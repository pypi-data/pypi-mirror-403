"""Network Interface object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_0_0.enums.type_id import TypeId


class NetworkInterface(OCSFBaseModel):
    """The Network Interface object describes the type and associated attributes of a network interface.

    See: https://schema.ocsf.io/1.0.0/objects/network_interface
    """

    type_id: TypeId = Field(..., description="The network interface type identifier.")
    hostname: Any | None = Field(
        default=None,
        description="The hostname associated with the network interface. [Recommended]",
    )
    ip: Any | None = Field(
        default=None,
        description="The IP address associated with the network interface. [Recommended]",
    )
    mac: Any | None = Field(
        default=None, description="The MAC address of the network interface. [Recommended]"
    )
    name: str | None = Field(default=None, description="The name of the network interface.")
    namespace: str | None = Field(
        default=None,
        description="The namespace is useful in merger or acquisition situations. For example, when similar entities exists that you need to keep separate.",
    )
    subnet_prefix: int | None = Field(
        default=None,
        description="The subnet prefix length determines the number of bits used to represent the network part of the IP address. The remaining bits are reserved for identifying individual hosts within that subnet.",
    )
    type_: str | None = Field(default=None, description="The type of network interface.")
    uid: str | None = Field(
        default=None, description="The unique identifier for the network interface."
    )
