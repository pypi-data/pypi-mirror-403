"""Subject Alternative Name object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class San(OCSFBaseModel):
    """The Subject Alternative name (SAN) object describes a SAN secured by a digital certificate

    See: https://schema.ocsf.io/1.2.0/objects/san
    """

    name: str = Field(..., description="Name of SAN (e.g. The actual IP Address or domain.)")
    type_: str = Field(..., description="Type descriptor of SAN (e.g. IP Address/domain/etc.)")
