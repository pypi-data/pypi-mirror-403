"""TLS Extension object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.enums.type_id import TypeId


class TlsExtension(OCSFBaseModel):
    """The TLS Extension object describes additional attributes that extend the base Transport Layer Security (TLS) object.

    See: https://schema.ocsf.io/1.6.0/objects/tls_extension
    """

    type_id: TypeId = Field(
        ...,
        description="The TLS extension type identifier. See <a target='_blank' href='https://datatracker.ietf.org/doc/html/rfc8446#page-35'>The Transport Layer Security (TLS) extension page</a>.",
    )
    data: dict[str, Any] | None = Field(
        default=None,
        description="The data contains information specific to the particular extension type. [Recommended]",
    )
    type_: str | None = Field(
        default=None, description="The TLS extension type. For example: <code>Server Name</code>."
    )
