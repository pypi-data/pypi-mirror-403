"""Evidence Artifacts object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_1_0.objects.actor import Actor
    from ocsf.v1_1_0.objects.api import Api
    from ocsf.v1_1_0.objects.dns_query import DnsQuery
    from ocsf.v1_1_0.objects.file import File
    from ocsf.v1_1_0.objects.network_connection_info import NetworkConnectionInfo
    from ocsf.v1_1_0.objects.network_endpoint import NetworkEndpoint
    from ocsf.v1_1_0.objects.process import Process


class Evidences(OCSFBaseModel):
    """A collection of evidence artifacts associated to the activity/activities that triggered a security detection.

    See: https://schema.ocsf.io/1.1.0/objects/evidences
    """

    actor: Actor | None = Field(
        default=None,
        description="Describes details about the user/role/process that was the source of the activity that triggered the detection. [Recommended]",
    )
    api: Api | None = Field(
        default=None,
        description="Describes details about the API call associated to the activity that triggered the detection. [Recommended]",
    )
    connection_info: NetworkConnectionInfo | None = Field(
        default=None,
        description="Describes details about the network connection associated to the activity that triggered the detection. [Recommended]",
    )
    data: dict[str, Any] | None = Field(
        default=None,
        description="Additional evidence data that is not accounted for in the specific evidence attributes.<code> Use only when absolutely necessary.</code>",
    )
    dst_endpoint: NetworkEndpoint | None = Field(
        default=None,
        description="Describes details about the destination of the network activity that triggered the detection. [Recommended]",
    )
    file: File | None = Field(
        default=None,
        description="Describes details about the file associated to the activity that triggered the detection. [Recommended]",
    )
    process: Process | None = Field(
        default=None,
        description="Describes details about the process associated to the activity that triggered the detection. [Recommended]",
    )
    query: DnsQuery | None = Field(
        default=None,
        description="Describes details about the DNS query associated to the activity that triggered the detection. [Recommended]",
    )
    src_endpoint: NetworkEndpoint | None = Field(
        default=None,
        description="Describes details about the source of the network activity that triggered the detection. [Recommended]",
    )
