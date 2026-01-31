"""Base classes for all OCSF models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class OCSFBaseModel(BaseModel):
    """Base model for all OCSF objects and events.

    Configures Pydantic for OCSF compatibility:
    - extra="allow" captures unmapped fields
    - use_enum_values=True serializes enums as integers
    """

    model_config = ConfigDict(
        populate_by_name=True,
        validate_default=True,
        extra="allow",
        str_strip_whitespace=True,
        use_enum_values=True,
    )
