"""Encryption Details object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.algorithm_id import AlgorithmId


class EncryptionDetails(OCSFBaseModel):
    """Details about the encrytpion methodology utilized.

    See: https://schema.ocsf.io/1.5.0/objects/encryption_details
    """

    algorithm: str | None = Field(
        default=None,
        description="The encryption algorithm used, normalized to the caption of 'algorithm_id",
    )
    algorithm_id: AlgorithmId | None = Field(
        default=None, description="The encryption algorithm used. [Recommended]"
    )
    key_length: int | None = Field(
        default=None, description="The length of the encryption key used."
    )
    key_uid: str | None = Field(
        default=None,
        description="The unique identifier of the key used for encrpytion. For example, AWS KMS Key ARN.",
    )
    type_: str | None = Field(
        default=None, description="The type of the encryption used. [Recommended]"
    )
