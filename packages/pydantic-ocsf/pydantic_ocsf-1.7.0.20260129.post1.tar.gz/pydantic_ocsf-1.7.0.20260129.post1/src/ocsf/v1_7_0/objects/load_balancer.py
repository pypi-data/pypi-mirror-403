"""Load Balancer object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.objects.endpoint_connection import EndpointConnection
    from ocsf.v1_7_0.objects.metric import Metric
    from ocsf.v1_7_0.objects.network_endpoint import NetworkEndpoint


class LoadBalancer(OCSFBaseModel):
    """The load balancer object describes the load balancer entity and contains additional information regarding the distribution of traffic across a network.

    See: https://schema.ocsf.io/1.7.0/objects/load_balancer
    """

    classification: str | None = Field(
        default=None, description="The request classification as defined by the load balancer."
    )
    code: int | None = Field(
        default=None,
        description="The numeric response status code detailing the connection from the load balancer to the destination target. [Recommended]",
    )
    dst_endpoint: NetworkEndpoint | None = Field(
        default=None,
        description="The destination to which the load balancer is distributing traffic. [Recommended]",
    )
    endpoint_connections: list[EndpointConnection] | None = Field(
        default=None,
        description="An object detailing the load balancer connection attempts and responses. [Recommended]",
    )
    error_message: str | None = Field(default=None, description="The load balancer error message.")
    ip: Any | None = Field(
        default=None,
        description="The IP address of the load balancer node that handled the client request. Note: the load balancer may have other IP addresses, and this is not an IP address of the target/distribution endpoint - see <code>dst_endpoint</code>.",
    )
    message: str | None = Field(default=None, description="The load balancer message.")
    metrics: list[Metric] | None = Field(
        default=None, description="General purpose metrics associated with the load balancer."
    )
    name: str | None = Field(default=None, description="The name of the load balancer.")
    status_detail: str | None = Field(
        default=None,
        description="The status detail contains additional status information about the load balancer distribution event.",
    )
    uid: str | None = Field(
        default=None, description="The unique identifier for the load balancer."
    )
