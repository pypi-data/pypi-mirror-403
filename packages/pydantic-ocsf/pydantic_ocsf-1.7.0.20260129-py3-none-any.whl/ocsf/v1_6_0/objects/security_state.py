"""Security State object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.enums.state_id import StateId


class SecurityState(OCSFBaseModel):
    """The Security State object describes the security related state of a managed entity.

    See: https://schema.ocsf.io/1.6.0/objects/security_state
    """

    state: str | None = Field(
        default=None,
        description="The security state, normalized to the caption of the state_id value. In the case of 'Other', it is defined by the source.",
    )
    state_id: StateId | None = Field(
        default=None, description="The security state of the managed entity. [Recommended]"
    )
