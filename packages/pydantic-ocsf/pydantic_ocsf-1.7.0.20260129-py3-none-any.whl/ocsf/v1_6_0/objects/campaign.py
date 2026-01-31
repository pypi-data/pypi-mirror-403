"""Campaign object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Campaign(OCSFBaseModel):
    """Campaign represent organized efforts by threat actors to achieve malicious objectives over a period, often characterized by shared tactics, techniques, and procedures (TTPs).

    See: https://schema.ocsf.io/1.6.0/objects/campaign
    """

    name: str = Field(
        ..., description="The name of a specific campaign associated with a cyber threat."
    )
