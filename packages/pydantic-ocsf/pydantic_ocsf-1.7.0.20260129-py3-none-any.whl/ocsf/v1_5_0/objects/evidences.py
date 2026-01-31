"""Evidence Artifacts object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.verdict_id import VerdictId
    from ocsf.v1_5_0.objects.actor import Actor
    from ocsf.v1_5_0.objects.api import Api
    from ocsf.v1_5_0.objects.container import Container
    from ocsf.v1_5_0.objects.database import Database
    from ocsf.v1_5_0.objects.databucket import Databucket
    from ocsf.v1_5_0.objects.device import Device
    from ocsf.v1_5_0.objects.dns_query import DnsQuery
    from ocsf.v1_5_0.objects.email import Email
    from ocsf.v1_5_0.objects.file import File
    from ocsf.v1_5_0.objects.http_request import HttpRequest
    from ocsf.v1_5_0.objects.http_response import HttpResponse
    from ocsf.v1_5_0.objects.ja4_fingerprint import Ja4Fingerprint
    from ocsf.v1_5_0.objects.job import Job
    from ocsf.v1_5_0.objects.network_connection_info import NetworkConnectionInfo
    from ocsf.v1_5_0.objects.network_endpoint import NetworkEndpoint
    from ocsf.v1_5_0.objects.process import Process
    from ocsf.v1_5_0.objects.resource_details import ResourceDetails
    from ocsf.v1_5_0.objects.script import Script
    from ocsf.v1_5_0.objects.tls import Tls
    from ocsf.v1_5_0.objects.url import Url
    from ocsf.v1_5_0.objects.user import User


class Evidences(OCSFBaseModel):
    """A collection of evidence artifacts associated to the activity/activities that triggered a security detection.

    See: https://schema.ocsf.io/1.5.0/objects/evidences
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
    container: Container | None = Field(
        default=None,
        description="Describes details about the container associated to the activity that triggered the detection. [Recommended]",
    )
    data: dict[str, Any] | None = Field(
        default=None,
        description="Additional evidence data that is not accounted for in the specific evidence attributes.<code> Use only when absolutely necessary.</code>",
    )
    database: Database | None = Field(
        default=None,
        description="Describes details about the database associated to the activity that triggered the detection. [Recommended]",
    )
    databucket: Databucket | None = Field(
        default=None,
        description="Describes details about the databucket associated to the activity that triggered the detection. [Recommended]",
    )
    device: Device | None = Field(
        default=None,
        description="An addressable device, computer system or host associated to the activity that triggered the detection. [Recommended]",
    )
    dst_endpoint: NetworkEndpoint | None = Field(
        default=None,
        description="Describes details about the destination of the network activity that triggered the detection. [Recommended]",
    )
    email: Email | None = Field(
        default=None,
        description="The email object associated to the activity that triggered the detection. [Recommended]",
    )
    file: File | None = Field(
        default=None,
        description="Describes details about the file associated to the activity that triggered the detection. [Recommended]",
    )
    http_request: HttpRequest | None = Field(
        default=None,
        description="Describes details about the http request associated to the activity that triggered the detection. [Recommended]",
    )
    http_response: HttpResponse | None = Field(
        default=None,
        description="Describes details about the http response associated to the activity that triggered the detection. [Recommended]",
    )
    ja4_fingerprint_list: list[Ja4Fingerprint] | None = Field(
        default=None,
        description="Describes details about the JA4+ fingerprints that triggered the detection. [Recommended]",
    )
    job: Job | None = Field(
        default=None,
        description="Describes details about the scheduled job that was associated with the activity that triggered the detection. [Recommended]",
    )
    name: str | None = Field(
        default=None,
        description="The naming convention or type identifier of the evidence associated with the security detection. For example, the <code>@odata.type</code> from Microsoft Graph Alerts V2 or <code>display_name</code> from CrowdStrike Falcon Incident Behaviors.",
    )
    process: Process | None = Field(
        default=None,
        description="Describes details about the process associated to the activity that triggered the detection. [Recommended]",
    )
    query: DnsQuery | None = Field(
        default=None,
        description="Describes details about the DNS query associated to the activity that triggered the detection. [Recommended]",
    )
    resources: list[ResourceDetails] | None = Field(
        default=None,
        description="Describes details about the cloud resources directly related to activity that triggered the detection. For resources impacted by the detection, use <code>Affected Resources</code> at the top-level of the finding. [Recommended]",
    )
    script: Script | None = Field(
        default=None,
        description="Describes details about the script that was associated with the activity that triggered the detection. [Recommended]",
    )
    src_endpoint: NetworkEndpoint | None = Field(
        default=None,
        description="Describes details about the source of the network activity that triggered the detection. [Recommended]",
    )
    tls: Tls | None = Field(
        default=None,
        description="Describes details about the Transport Layer Security (TLS) activity that triggered the detection. [Recommended]",
    )
    uid: str | None = Field(
        default=None,
        description="The unique identifier of the evidence associated with the security detection. For example, the <code>activity_id</code> from CrowdStrike Falcon Alerts or <code>behavior_id</code> from CrowdStrike Falcon Incident Behaviors.",
    )
    url: Url | None = Field(
        default=None,
        description="The URL object that pertains to the event or object associated to the activity that triggered the detection. [Recommended]",
    )
    user: User | None = Field(
        default=None,
        description="Describes details about the user that was the target or somehow else associated with the activity that triggered the detection. [Recommended]",
    )
    verdict: str | None = Field(
        default=None,
        description="The normalized verdict of the evidence associated with the security detection. ",
    )
    verdict_id: VerdictId | None = Field(
        default=None,
        description="The normalized verdict (or status) ID of the evidence associated with the security detection. For example, Microsoft Graph Security Alerts contain a <code>verdict</code> enumeration for each type of <code>evidence</code> associated with the Alert. This is typically set by an automated investigation process or an analyst/investigator assigned to the finding.",
    )
