"""DCE/RPC object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_2_0.objects.rpc_interface import RpcInterface


class DceRpc(OCSFBaseModel):
    """The DCE/RPC, or Distributed Computing Environment/Remote Procedure Call, object describes the remote procedure call system for distributed computing environments. Defined by D3FEND <a target='_blank' href='https://d3fend.mitre.org/dao/artifact/d3f:RemoteProcedureCall/'>d3f:RemoteProcedureCall</a>.

    See: https://schema.ocsf.io/1.2.0/objects/dce_rpc
    """

    flags: list[str] = Field(..., description="The list of interface flags.")
    rpc_interface: RpcInterface = Field(
        ...,
        description="The RPC Interface object describes the details pertaining to the remote procedure call interface.",
    )
    command: str | None = Field(
        default=None, description="The request command (e.g. REQUEST, BIND). [Recommended]"
    )
    command_response: str | None = Field(
        default=None,
        description="The reply to the request command (e.g. RESPONSE, BINDACK or FAULT). [Recommended]",
    )
    opnum: int | None = Field(
        default=None,
        description="An operation number used to identify a specific remote procedure call (RPC) method or a method in an interface. [Recommended]",
    )
