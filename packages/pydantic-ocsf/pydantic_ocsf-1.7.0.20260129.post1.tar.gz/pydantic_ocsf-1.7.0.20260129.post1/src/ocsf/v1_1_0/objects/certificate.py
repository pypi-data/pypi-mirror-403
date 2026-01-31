"""Digital Certificate object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_1_0.objects.fingerprint import Fingerprint


class Certificate(OCSFBaseModel):
    """The Digital Certificate, also known as a Public Key Certificate, object contains information about the ownership and usage of a public key. It serves as a means to establish trust in the authenticity and integrity of the public key and the associated entity. Defined by D3FEND <a target='_blank' href='https://d3fend.mitre.org/dao/artifact/d3f:Certificate/'>d3f:Certificate</a>.

    See: https://schema.ocsf.io/1.1.0/objects/certificate
    """

    fingerprints: list[Fingerprint] = Field(
        ..., description="The fingerprint list of the certificate."
    )
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
    subject: str | None = Field(
        default=None, description="The certificate subject distinguished name. [Recommended]"
    )
    uid: str | None = Field(default=None, description="The unique identifier of the certificate.")
    version: str | None = Field(default=None, description="The certificate version. [Recommended]")
