"""Network Connection Information object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_1_0.enums.boundary_id import BoundaryId
    from ocsf.v1_1_0.enums.direction_id import DirectionId
    from ocsf.v1_1_0.enums.protocol_ver_id import ProtocolVerId
    from ocsf.v1_1_0.objects.session import Session


class NetworkConnectionInfo(OCSFBaseModel):
    """The Network Connection Information object describes characteristics of a network connection. Defined by D3FEND <a target='_blank' href='https://d3fend.mitre.org/dao/artifact/d3f:NetworkSession/'>d3f:NetworkSession</a>.

    See: https://schema.ocsf.io/1.1.0/objects/network_connection_info
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
        description="<p>The normalized identifier of the boundary of the connection. </p><p> For cloud connections, this translates to the traffic-boundary (same VPC, through IGW, etc.). For traditional networks, this is described as Local, Internal, or External.</p>",
    )
    direction: str | None = Field(
        default=None,
        description="The direction of the initiated connection, traffic, or email, normalized to the caption of the direction_id value. In the case of 'Other', it is defined by the event source.",
    )
    protocol_name: str | None = Field(
        default=None,
        description="The TCP/IP protocol name in lowercase, as defined by the Internet Assigned Numbers Authority (IANA). See <a target='_blank' href='https://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml'>Protocol Numbers</a>. For example: <code>tcp</code> or <code>udp</code>.",
    )
    protocol_num: int | None = Field(
        default=None,
        description="The TCP/IP protocol number, as defined by the Internet Assigned Numbers Authority (IANA). Use -1 if the protocol is not defined by IANA. See <a target='_blank' href='https://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml'>Protocol Numbers</a>. For example: <code>6</code> for TCP and <code>17</code> for UDP. [Recommended]",
    )
    protocol_ver: str | None = Field(default=None, description="The Internet Protocol version.")
    protocol_ver_id: ProtocolVerId | None = Field(
        default=None, description="The Internet Protocol version identifier."
    )
    session: Session | None = Field(
        default=None, description="The authenticated user or service session."
    )
    tcp_flags: int | None = Field(
        default=None, description="The network connection TCP header flags (i.e., control bits)."
    )
    uid: str | None = Field(default=None, description="The unique identifier of the connection.")
