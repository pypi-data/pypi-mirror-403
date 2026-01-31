"""Endpoint Connection object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.objects.network_endpoint import NetworkEndpoint


class EndpointConnection(OCSFBaseModel):
    """The Endpoint Connection object contains information detailing a connection attempt to an endpoint.

    See: https://schema.ocsf.io/1.6.0/objects/endpoint_connection
    """

    code: int | None = Field(
        default=None,
        description="A numerical response status code providing details about the connection. [Recommended]",
    )
    network_endpoint: NetworkEndpoint | None = Field(
        default=None, description="Provides characteristics of the network endpoint. [Recommended]"
    )
