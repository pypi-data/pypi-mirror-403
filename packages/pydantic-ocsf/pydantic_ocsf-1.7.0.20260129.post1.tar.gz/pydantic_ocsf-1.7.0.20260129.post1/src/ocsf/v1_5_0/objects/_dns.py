"""DNS object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Dns(OCSFBaseModel):
    """The Domain Name System (DNS) object represents the shared information associated with the DNS query and answer objects.

    See: https://schema.ocsf.io/1.5.0/objects/_dns
    """

    class_: str | None = Field(
        default=None,
        description="The class of resource records being queried. See <a target='_blank' href='https://www.rfc-editor.org/rfc/rfc1035.txt'>RFC1035</a>. For example: <code>IN</code>. [Recommended]",
    )
    packet_uid: int | None = Field(
        default=None,
        description="The DNS packet identifier assigned by the program that generated the query. The identifier is copied to the response. [Recommended]",
    )
    type_: str | None = Field(
        default=None,
        description="The type of resource records being queried. See <a target='_blank' href='https://www.rfc-editor.org/rfc/rfc1035.txt'>RFC1035</a>. For example: A, AAAA, CNAME, MX, and NS. [Recommended]",
    )
