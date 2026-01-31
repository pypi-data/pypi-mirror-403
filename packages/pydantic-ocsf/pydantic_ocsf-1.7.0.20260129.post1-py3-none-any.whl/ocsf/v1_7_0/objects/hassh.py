"""HASSH object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.objects.fingerprint import Fingerprint


class Hassh(OCSFBaseModel):
    """The HASSH object contains SSH network fingerprinting values for specific client/server implementations. It provides a standardized way of identifying and categorizing SSH connections based on their unique characteristics and behavior.

    See: https://schema.ocsf.io/1.7.0/objects/hassh
    """

    fingerprint: Fingerprint = Field(
        ...,
        description="The hash of the key exchange, encryption, authentication and compression algorithms.",
    )
    algorithm: str | None = Field(
        default=None,
        description="The concatenation of key exchange, encryption, authentication and compression algorithms (separated by ';'). NOTE: This is not the underlying algorithm for the hash implementation. [Recommended]",
    )
