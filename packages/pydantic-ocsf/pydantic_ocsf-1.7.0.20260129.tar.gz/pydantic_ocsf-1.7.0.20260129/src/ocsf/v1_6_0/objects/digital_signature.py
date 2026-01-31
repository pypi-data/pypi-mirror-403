"""Digital Signature object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.enums.algorithm_id import AlgorithmId
    from ocsf.v1_6_0.enums.state_id import StateId
    from ocsf.v1_6_0.objects.certificate import Certificate
    from ocsf.v1_6_0.objects.fingerprint import Fingerprint


class DigitalSignature(OCSFBaseModel):
    """The Digital Signature object contains information about the cryptographic mechanism used to verify the authenticity, integrity, and origin of the file or application.

    See: https://schema.ocsf.io/1.6.0/objects/digital_signature
    """

    algorithm_id: AlgorithmId = Field(
        ..., description="The identifier of the normalized digital signature algorithm."
    )
    algorithm: str | None = Field(
        default=None,
        description="The digital signature algorithm used to create the signature, normalized to the caption of 'algorithm_id'. In the case of 'Other', it is defined by the event source.",
    )
    certificate: Certificate | None = Field(
        default=None,
        description="The certificate object containing information about the digital certificate. [Recommended]",
    )
    created_time: int | None = Field(
        default=None, description="The time when the digital signature was created."
    )
    developer_uid: str | None = Field(
        default=None, description="The developer ID on the certificate that signed the file."
    )
    digest: Fingerprint | None = Field(
        default=None,
        description="The message digest attribute contains the fixed length message hash representation and the corresponding hashing algorithm information.",
    )
    state: str | None = Field(
        default=None,
        description="The digital signature state defines the signature state, normalized to the caption of 'state_id'. In the case of 'Other', it is defined by the event source.",
    )
    state_id: StateId | None = Field(
        default=None, description="The normalized identifier of the signature state."
    )
