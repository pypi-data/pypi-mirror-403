"""DNS Query object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.enums.opcode_id import OpcodeId


class DnsQuery(OCSFBaseModel):
    """The DNS query object represents a specific request made to the Domain Name System (DNS) to retrieve information about a domain or perform a DNS operation. This object encapsulates the necessary attributes and methods to construct and send DNS queries, specify the query type (e.g., A, AAAA, MX).

    See: https://schema.ocsf.io/1.6.0/objects/dns_query
    """

    hostname: Any = Field(
        ...,
        description="The hostname or domain being queried. For example: <code>www.example.com</code>",
    )
    class_: str | None = Field(
        default=None,
        description="The class of resource records being queried. See <a target='_blank' href='https://www.rfc-editor.org/rfc/rfc1035.txt'>RFC1035</a>. For example: <code>IN</code>. [Recommended]",
    )
    opcode: str | None = Field(
        default=None, description="The DNS opcode specifies the type of the query message."
    )
    opcode_id: OpcodeId | None = Field(
        default=None,
        description="The DNS opcode ID specifies the normalized query message type as defined in <a target='_blank' href='https://www.rfc-editor.org/rfc/rfc5395.html'>RFC-5395</a>. [Recommended]",
    )
    packet_uid: int | None = Field(
        default=None,
        description="The DNS packet identifier assigned by the program that generated the query. The identifier is copied to the response. [Recommended]",
    )
    type_: str | None = Field(
        default=None,
        description="The type of resource records being queried. See <a target='_blank' href='https://www.rfc-editor.org/rfc/rfc1035.txt'>RFC1035</a>. For example: A, AAAA, CNAME, MX, and NS. [Recommended]",
    )
