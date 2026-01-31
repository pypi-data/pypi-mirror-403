"""Actor object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.objects.authorization import Authorization
    from ocsf.v1_6_0.objects.idp import Idp
    from ocsf.v1_6_0.objects.process import Process
    from ocsf.v1_6_0.objects.session import Session
    from ocsf.v1_6_0.objects.user import User


class Actor(OCSFBaseModel):
    """The Actor object contains details about the user, role, application, service, or process that initiated or performed a specific activity. Note that Actor is not the threat actor of a campaign but may be part of a campaign.

    See: https://schema.ocsf.io/1.6.0/objects/actor
    """

    app_name: str | None = Field(
        default=None,
        description="The client application or service that initiated the activity. This can be in conjunction with the <code>user</code> if present.  Note that <code>app_name</code> is distinct from the <code>process</code> if present.",
    )
    app_uid: str | None = Field(
        default=None,
        description="The unique identifier of the client application or service that initiated the activity. This can be in conjunction with the <code>user</code> if present. Note that <code>app_name</code> is distinct from the <code>process.pid</code> or <code>process.uid</code> if present.",
    )
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
