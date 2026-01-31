"""Digital Certificate object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.objects.fingerprint import Fingerprint
    from ocsf.v1_6_0.objects.san import San


class Certificate(OCSFBaseModel):
    """The Digital Certificate, also known as a Public Key Certificate, object contains information about the ownership and usage of a public key. It serves as a means to establish trust in the authenticity and integrity of the public key and the associated entity.

    See: https://schema.ocsf.io/1.6.0/objects/certificate
    """

    issuer: str = Field(..., description="The certificate issuer distinguished name.")
    serial_number: str = Field(
        ...,
        description="The serial number of the certificate used to create the digital signature.",
    )
    created_time: int | None = Field(
        default=None, description="The time when the certificate was created. [Recommended]"
    )
    expiration_time: int | None = Field(
        default=None, description="The expiration time of the certificate. [Recommended]"
    )
    fingerprints: list[Fingerprint] | None = Field(
        default=None, description="The fingerprint list of the certificate. [Recommended]"
    )
    is_self_signed: bool | None = Field(
        default=None,
        description="Denotes whether a digital certificate is self-signed or signed by a known certificate authority (CA). [Recommended]",
    )
    sans: list[San] | None = Field(
        default=None,
        description="The list of subject alternative names that are secured by a specific certificate.",
    )
    subject: str | None = Field(
        default=None, description="The certificate subject distinguished name. [Recommended]"
    )
    uid: str | None = Field(default=None, description="The unique identifier of the certificate.")
    version: str | None = Field(default=None, description="The certificate version. [Recommended]")
