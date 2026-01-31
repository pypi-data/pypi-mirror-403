"""RPC Interface object."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ocsf._base import OCSFBaseModel


class RpcInterface(OCSFBaseModel):
    """The RPC Interface represents the remote procedure call interface used in the DCE/RPC session.

    See: https://schema.ocsf.io/1.7.0/objects/rpc_interface
    """

    uuid: Any = Field(
        ..., description="The unique identifier of the particular remote procedure or service."
    )
    version: str = Field(
        ..., description="The version of the DCE/RPC protocol being used in the session."
    )
    ack_reason: int | None = Field(
        default=None,
        description="An integer that provides a reason code or additional information about the acknowledgment result. [Recommended]",
    )
    ack_result: int | None = Field(
        default=None,
        description="An integer that denotes the acknowledgment result of the DCE/RPC call. [Recommended]",
    )
