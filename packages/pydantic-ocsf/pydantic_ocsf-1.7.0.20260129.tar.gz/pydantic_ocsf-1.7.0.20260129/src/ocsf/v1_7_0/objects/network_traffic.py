"""Network Traffic object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.objects.timespan import Timespan


class NetworkTraffic(OCSFBaseModel):
    """The Network Traffic object describes characteristics of network traffic over a time period. The metrics represent network data transferred between source and destination during an observation window.

    See: https://schema.ocsf.io/1.7.0/objects/network_traffic
    """

    bytes: int | None = Field(
        default=None,
        description="The total number of bytes transferred in both directions (sum of bytes_in and bytes_out). [Recommended]",
    )
    bytes_in: int | None = Field(
        default=None,
        description="The number of bytes sent from the destination to the source (inbound direction).",
    )
    bytes_missed: int | None = Field(
        default=None,
        description="The number of bytes that were missed during observation, typically due to packet loss or sampling limitations.",
    )
    bytes_out: int | None = Field(
        default=None,
        description="The number of bytes sent from the source to the destination (outbound direction).",
    )
    chunks: int | None = Field(
        default=None,
        description="The total number of chunks transferred in both directions (sum of chunks_in and chunks_out).",
    )
    chunks_in: int | None = Field(
        default=None,
        description="The number of chunks sent from the destination to the source (inbound direction).",
    )
    chunks_out: int | None = Field(
        default=None,
        description="The number of chunks sent from the source to the destination (outbound direction).",
    )
    end_time: int | None = Field(
        default=None, description="The end time of the observation or reporting period."
    )
    packets: int | None = Field(
        default=None,
        description="The total number of packets transferred in both directions (sum of packets_in and packets_out). [Recommended]",
    )
    packets_in: int | None = Field(
        default=None,
        description="The number of packets sent from the destination to the source (inbound direction).",
    )
    packets_out: int | None = Field(
        default=None,
        description="The number of packets sent from the source to the destination (outbound direction).",
    )
    start_time: int | None = Field(
        default=None, description="The start time of the observation or reporting period."
    )
    timespan: Timespan | None = Field(
        default=None,
        description="The time span object representing the duration of the observation or reporting period.",
    )
