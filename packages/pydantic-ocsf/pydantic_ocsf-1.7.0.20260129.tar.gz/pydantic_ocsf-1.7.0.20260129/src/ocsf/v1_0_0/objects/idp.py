"""Identity Provider object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class Idp(OCSFBaseModel):
    """The Identity Provider object contains detailed information about a provider responsible for creating, maintaining, and managing identity information while offering authentication services to applications. An Identity Provider (IdP) serves as a trusted authority that verifies the identity of users and issues authentication tokens or assertions to enable secure access to applications or services.

    See: https://schema.ocsf.io/1.0.0/objects/idp
    """

    name: str | None = Field(default=None, description="The name of the identity provider.")
    uid: str | None = Field(
        default=None, description="The unique identifier of the identity provider."
    )
