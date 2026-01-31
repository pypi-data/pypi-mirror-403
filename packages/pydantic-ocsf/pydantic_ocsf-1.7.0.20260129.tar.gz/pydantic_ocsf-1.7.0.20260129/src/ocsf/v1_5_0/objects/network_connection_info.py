"""Network Connection Information object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.boundary_id import BoundaryId
    from ocsf.v1_5_0.enums.direction_id import DirectionId
    from ocsf.v1_5_0.enums.protocol_ver_id import ProtocolVerId
    from ocsf.v1_5_0.objects.session import Session


class NetworkConnectionInfo(OCSFBaseModel):
    """The Network Connection Information object describes characteristics of an OSI Transport Layer communication, including TCP and UDP.

    See: https://schema.ocsf.io/1.5.0/objects/network_connection_info
    """

    direction_id: DirectionId = Field(
        ...,
        description="The normalized identifier of the direction of the initiated connection, traffic, or email.",
    )
    boundary: str | None = Field(
        default=None,
        description="The boundary of the connection, normalized to the caption of 'boundary_id'. In the case of 'Other', it is defined by the event source. <p> For cloud connections, this translates to the traffic-boundary(same VPC, through IGW, etc.). For traditional networks, this is described as Local, Internal, or External.</p>",
    )
    boundary_id: BoundaryId | None = Field(
        default=None,
        description="<p>The normalized identifier of the boundary of the connection. </p><p> For cloud connections, this translates to the traffic-boundary (same VPC, through IGW, etc.). For traditional networks, this is described as Local, Internal, or External.</p> [Recommended]",
    )
    community_uid: str | None = Field(
        default=None, description="The Community ID of the network connection."
    )
    direction: str | None = Field(
        default=None,
        description="The direction of the initiated connection, traffic, or email, normalized to the caption of the direction_id value. In the case of 'Other', it is defined by the event source.",
    )
    flag_history: str | None = Field(
        default=None,
        description="The Connection Flag History summarizes events in a network connection. For example flags <code> ShAD </code> representing SYN, SYN/ACK, ACK and Data exchange.",
    )
    protocol_name: str | None = Field(
        default=None,
        description="The IP protocol name in lowercase, as defined by the Internet Assigned Numbers Authority (IANA). For example: <code>tcp</code> or <code>udp</code>. [Recommended]",
    )
    protocol_num: int | None = Field(
        default=None,
        description="The IP protocol number, as defined by the Internet Assigned Numbers Authority (IANA). For example: <code>6</code> for TCP and <code>17</code> for UDP. [Recommended]",
    )
    protocol_ver: str | None = Field(default=None, description="The Internet Protocol version.")
    protocol_ver_id: ProtocolVerId | None = Field(
        default=None, description="The Internet Protocol version identifier. [Recommended]"
    )
    session: Session | None = Field(
        default=None, description="The authenticated user or service session."
    )
    tcp_flags: int | None = Field(
        default=None, description="The network connection TCP header flags (i.e., control bits)."
    )
    uid: str | None = Field(
        default=None, description="The unique identifier of the connection. [Recommended]"
    )
