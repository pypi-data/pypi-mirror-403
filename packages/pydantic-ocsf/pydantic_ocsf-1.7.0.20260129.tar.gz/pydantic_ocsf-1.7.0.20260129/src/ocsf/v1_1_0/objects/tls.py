"""Transport Layer Security (TLS) object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_1_0.objects.certificate import Certificate
    from ocsf.v1_1_0.objects.fingerprint import Fingerprint
    from ocsf.v1_1_0.objects.san import San
    from ocsf.v1_1_0.objects.tls_extension import TlsExtension


class Tls(OCSFBaseModel):
    """The Transport Layer Security (TLS) object describes the negotiated TLS protocol used for secure communications over an establish network connection.

    See: https://schema.ocsf.io/1.1.0/objects/tls
    """

    version: str = Field(..., description="The TLS protocol version.")
    alert: int | None = Field(
        default=None,
        description="The integer value of TLS alert if present. The alerts are defined in the TLS specification in <a target='_blank' href='https://datatracker.ietf.org/doc/html/rfc2246'>RFC-2246</a>.",
    )
    certificate: Certificate | None = Field(
        default=None,
        description="The certificate object containing information about the digital certificate. [Recommended]",
    )
    certificate_chain: list[str] | None = Field(
        default=None,
        description="The Chain of Certificate Serial Numbers field provides a chain of Certificate Issuer Serial Numbers leading to the Root Certificate Issuer. [Recommended]",
    )
    cipher: str | None = Field(
        default=None, description="The negotiated cipher suite. [Recommended]"
    )
    client_ciphers: list[str] | None = Field(
        default=None,
        description="The client cipher suites that were exchanged during the TLS handshake negotiation. [Recommended]",
    )
    extension_list: list[TlsExtension] | None = Field(
        default=None, description="The list of TLS extensions."
    )
    handshake_dur: int | None = Field(
        default=None,
        description="The amount of total time for the TLS handshake to complete after the TCP connection is established, including client-side delays, in milliseconds.",
    )
    ja3_hash: Fingerprint | None = Field(
        default=None, description="The MD5 hash of a JA3 string. [Recommended]"
    )
    ja3s_hash: Fingerprint | None = Field(
        default=None, description="The MD5 hash of a JA3S string. [Recommended]"
    )
    key_length: int | None = Field(default=None, description="The length of the encryption key.")
    sans: list[San] | None = Field(
        default=None,
        description="The list of subject alternative names that are secured by a specific certificate.",
    )
    server_ciphers: list[str] | None = Field(
        default=None,
        description="The server cipher suites that were exchanged during the TLS handshake negotiation.",
    )
    sni: str | None = Field(
        default=None,
        description=" The Server Name Indication (SNI) extension sent by the client. [Recommended]",
    )
    tls_extension_list: list[TlsExtension] | None = Field(
        default=None, description="The list of TLS extensions."
    )
