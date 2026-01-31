"""Fingerprint object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_2_0.enums.algorithm_id import AlgorithmId


class Fingerprint(OCSFBaseModel):
    """The Fingerprint object provides detailed information about a digital fingerprint, which is a compact representation of data used to identify a longer piece of information, such as a public key or file content. It contains the algorithm and value of the fingerprint, enabling efficient and reliable identification of the associated data.

    See: https://schema.ocsf.io/1.2.0/objects/fingerprint
    """

    algorithm_id: AlgorithmId = Field(
        ...,
        description="The identifier of the normalized hash algorithm, which was used to create the digital fingerprint.",
    )
    value: Any = Field(..., description="The digital fingerprint value.")
    algorithm: str | None = Field(
        default=None,
        description="The hash algorithm used to create the digital fingerprint, normalized to the caption of 'algorithm_id'. In the case of 'Other', it is defined by the event source.",
    )
