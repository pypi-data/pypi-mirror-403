"""Agent object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.enums.type_id import TypeId
    from ocsf.v1_7_0.objects.policy import Policy


class Agent(OCSFBaseModel):
    """An Agent (also known as a Sensor) is typically installed on an Operating System (OS) and serves as a specialized software component that can be designed to monitor, detect, collect, archive, or take action. These activities and possible actions are defined by the upstream system controlling the Agent and its intended purpose. For instance, an Agent can include Endpoint Detection & Response (EDR) agents, backup/disaster recovery sensors, Application Performance Monitoring or profiling sensors, and similar software.

    See: https://schema.ocsf.io/1.7.0/objects/agent
    """

    name: str | None = Field(
        default=None,
        description="The name of the agent or sensor. For example: <code>AWS SSM Agent</code>. [Recommended]",
    )
    policies: list[Policy] | None = Field(
        default=None,
        description="Describes the various policies that may be applied or enforced by an agent or sensor. E.g., Conditional Access, prevention, auto-update, tamper protection, destination configuration, etc.",
    )
    type_: str | None = Field(
        default=None,
        description="The normalized caption of the type_id value for the agent or sensor. In the case of 'Other' or 'Unknown', it is defined by the event source.",
    )
    type_id: TypeId | None = Field(
        default=None,
        description="The normalized representation of an agent or sensor. E.g., EDR, vulnerability management, APM, backup & recovery, etc. [Recommended]",
    )
    uid: str | None = Field(
        default=None,
        description="The UID of the agent or sensor, sometimes known as a Sensor ID or <code>aid</code>. [Recommended]",
    )
    uid_alt: str | None = Field(
        default=None,
        description="An alternative or contextual identifier for the agent or sensor, such as a configuration, organization, or license UID.",
    )
    vendor_name: str | None = Field(
        default=None,
        description="The company or author who created the agent or sensor. For example: <code>Crowdstrike</code>.",
    )
    version: str | None = Field(
        default=None,
        description="The semantic version of the agent or sensor, e.g., <code>7.101.50.0</code>.",
    )
