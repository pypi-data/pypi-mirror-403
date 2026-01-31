"""Network Traffic object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class NetworkTraffic(OCSFBaseModel):
    """The Network Traffic object describes characteristics of network traffic. Network traffic refers to data moving across a network at a given point of time. Defined by D3FEND <a target='_blank' href='https://d3fend.mitre.org/dao/artifact/d3f:NetworkTraffic/'>d3f:NetworkTraffic</a>.

    See: https://schema.ocsf.io/1.2.0/objects/network_traffic
    """

    bytes: int | None = Field(
        default=None, description="The total number of bytes (in and out). [Recommended]"
    )
    bytes_in: int | None = Field(
        default=None, description="The number of bytes sent from the destination to the source."
    )
    bytes_out: int | None = Field(
        default=None, description="The number of bytes sent from the source to the destination."
    )
    chunks: int | None = Field(default=None, description="The total number of chunks (in and out).")
    chunks_in: int | None = Field(
        default=None, description="The number of chunks sent from the destination to the source."
    )
    chunks_out: int | None = Field(
        default=None, description="The number of chunks sent from the source to the destination."
    )
    packets: int | None = Field(
        default=None, description="The total number of packets (in and out). [Recommended]"
    )
    packets_in: int | None = Field(
        default=None, description="The number of packets sent from the destination to the source."
    )
    packets_out: int | None = Field(
        default=None, description="The number of packets sent from the source to the destination."
    )
