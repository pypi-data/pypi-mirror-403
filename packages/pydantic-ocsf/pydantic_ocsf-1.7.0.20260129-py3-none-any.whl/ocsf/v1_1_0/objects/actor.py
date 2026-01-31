"""Actor object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_1_0.objects.authorization import Authorization
    from ocsf.v1_1_0.objects.idp import Idp
    from ocsf.v1_1_0.objects.process import Process
    from ocsf.v1_1_0.objects.session import Session
    from ocsf.v1_1_0.objects.user import User


class Actor(OCSFBaseModel):
    """The Actor object contains details about the user, role, or process that initiated or performed a specific activity.

    See: https://schema.ocsf.io/1.1.0/objects/actor
    """

    authorizations: list[Authorization] | None = Field(
        default=None,
        description="Provides details about an authorization, such as authorization outcome, and any associated policies related to the activity/event.",
    )
    idp: Idp | None = Field(
        default=None, description="This object describes details about the Identity Provider used."
    )
    invoked_by: str | None = Field(
        default=None,
        description="The name of the service that invoked the activity as described in the event.",
    )
    process: Process | None = Field(
        default=None, description="The process that initiated the activity. [Recommended]"
    )
    session: Session | None = Field(
        default=None, description="The user session from which the activity was initiated."
    )
    user: User | None = Field(
        default=None,
        description="The user that initiated the activity or the user context from which the activity was initiated. [Recommended]",
    )
