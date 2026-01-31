"""Application object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.risk_level_id import RiskLevelId
    from ocsf.v1_5_0.objects.graph import Graph
    from ocsf.v1_5_0.objects.group import Group
    from ocsf.v1_5_0.objects.key_value_object import KeyValueObject
    from ocsf.v1_5_0.objects.sbom import Sbom
    from ocsf.v1_5_0.objects.url import Url
    from ocsf.v1_5_0.objects.user import User


class Application(OCSFBaseModel):
    """An Application describes the details for an inventoried application as reported by an Application Security tool or other Developer-centric tooling. Applications can be defined as Kubernetes resources, Containerized resources, or application hosting-specific cloud sources such as AWS Elastic BeanStalk, AWS Lightsail, or Azure Logic Apps.

    See: https://schema.ocsf.io/1.5.0/objects/application
    """

    criticality: str | None = Field(
        default=None,
        description="The criticality of the application as defined by the event source.",
    )
    data: dict[str, Any] | None = Field(
        default=None, description="Additional data describing the application."
    )
    desc: str | None = Field(
        default=None,
        description="A description or commentary for an application, usually retrieved from an upstream system.",
    )
    group: Group | None = Field(
        default=None,
        description="The name of the related application or associated resource group.",
    )
    hostname: Any | None = Field(
        default=None, description="The fully qualified name of the application."
    )
    labels: list[str] | None = Field(
        default=None, description="The list of labels associated to the application."
    )
    name: str | None = Field(default=None, description="The name of the application. [Recommended]")
    owner: User | None = Field(
        default=None,
        description="The identity of the service or user account that owns the application. [Recommended]",
    )
    region: str | None = Field(default=None, description="The cloud region of the resource.")
    resource_relationship: Graph | None = Field(
        default=None,
        description="A graph representation showing how this application relates to and interacts with other entities in the environment. This can include parent/child relationships, dependencies, or other connections.",
    )
    risk_level: str | None = Field(
        default=None,
        description="The risk level, normalized to the caption of the risk_level_id value.",
    )
    risk_level_id: RiskLevelId | None = Field(
        default=None, description="The normalized risk level id."
    )
    risk_score: int | None = Field(
        default=None, description="The risk score as reported by the event source."
    )
    sbom: Sbom | None = Field(
        default=None,
        description="The Software Bill of Materials (SBOM) associated with the application",
    )
    tags: list[KeyValueObject] | None = Field(
        default=None,
        description="The list of tags; <code>{key:value}</code> pairs associated to the application.",
    )
    type_: str | None = Field(
        default=None,
        description="The type of application as defined by the event source, e.g., <code>GitHub</code>, <code>Azure Logic App</code>, or <code>Amazon Elastic BeanStalk</code>.",
    )
    uid: str | None = Field(
        default=None, description="The unique identifier for the application. [Recommended]"
    )
    uid_alt: str | None = Field(
        default=None,
        description="An alternative or contextual identifier for the application, such as a configuration, organization, or license UID.",
    )
    url: Url | None = Field(default=None, description="The URL of the application.")
    version: str | None = Field(
        default=None,
        description="The semantic version of the application, e.g., <code>1.7.4</code>.",
    )
