"""Port Information object."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ocsf._base import OCSFBaseModel


class PortInfo(OCSFBaseModel):
    """The Port Information object describes a port and its associated protocol details.

    See: https://schema.ocsf.io/1.6.0/objects/port_info
    """

    port: Any = Field(
        ...,
        description="The port number. For example: <code>80</code>, <code>443</code>, <code>22</code>.",
    )
    protocol_name: str | None = Field(
        default=None,
        description="The IP protocol name in lowercase, as defined by the Internet Assigned Numbers Authority (IANA). For example: <code>tcp</code> or <code>udp</code>. [Recommended]",
    )
    protocol_num: int | None = Field(
        default=None,
        description="The IP protocol number, as defined by the Internet Assigned Numbers Authority (IANA). For example: <code>6</code> for TCP and <code>17</code> for UDP.",
    )
