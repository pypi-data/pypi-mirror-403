"""CIS Control object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class CisControl(OCSFBaseModel):
    """The CIS Control (aka Critical Security Control) object describes a prioritized set of actions to protect your organization and data from cyber-attack vectors. The <a target='_blank' href='https://www.cisecurity.org/controls'>CIS Controls</a> are defined by the Center for Internet Security.

    See: https://schema.ocsf.io/1.1.0/objects/cis_control
    """

    name: str = Field(
        ...,
        description="The CIS Control name. For example: <i>4.8 Uninstall or Disable Unnecessary Services on Enterprise Assets and Software.</i>",
    )
    desc: str | None = Field(
        default=None,
        description="The CIS Control description. For example: <i>Uninstall or disable unnecessary services on enterprise assets and software, such as an unused file sharing service, web application module, or service function.</i>",
    )
    version: str | None = Field(
        default=None, description="The CIS Control version. For example: <i>v8</i>. [Recommended]"
    )
