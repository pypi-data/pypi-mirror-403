"""DNS Answer object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_1_0.enums.flag_ids import FlagIds


class DnsAnswer(OCSFBaseModel):
    """The DNS Answer object represents a specific response provided by the Domain Name System (DNS) when querying for information about a domain or performing a DNS operation. It encapsulates the relevant details and data returned by the DNS server in response to a query.

    See: https://schema.ocsf.io/1.1.0/objects/dns_answer
    """

    rdata: str = Field(
        ...,
        description="The data describing the DNS resource. The meaning of this data depends on the type and class of the resource record.",
    )
    class_: str | None = Field(
        default=None,
        description="The class of DNS data contained in this resource record. See <a target='_blank' href='https://www.rfc-editor.org/rfc/rfc1035.txt'>RFC1035</a>. For example: <code>IN</code>.",
    )
    flag_ids: list[FlagIds] | None = Field(
        default=None, description="The list of DNS answer header flag IDs."
    )
    flags: list[str] | None = Field(
        default=None, description="The list of DNS answer header flags."
    )
    packet_uid: int | None = Field(
        default=None,
        description="The DNS packet identifier assigned by the program that generated the query. The identifier is copied to the response. [Recommended]",
    )
    ttl: int | None = Field(
        default=None,
        description="The time interval that the resource record may be cached. Zero value means that the resource record can only be used for the transaction in progress, and should not be cached. [Recommended]",
    )
    type_: str | None = Field(
        default=None,
        description="The type of data contained in this resource record. See <a target='_blank' href='https://www.rfc-editor.org/rfc/rfc1035.txt'>RFC1035</a>. For example: <code>CNAME</code>.",
    )
