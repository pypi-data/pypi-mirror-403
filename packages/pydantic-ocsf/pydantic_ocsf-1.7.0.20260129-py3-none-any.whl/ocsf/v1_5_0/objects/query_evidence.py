"""Query Evidence object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.query_type_id import QueryTypeId
    from ocsf.v1_5_0.enums.tcp_state_id import TcpStateId
    from ocsf.v1_5_0.objects.file import File
    from ocsf.v1_5_0.objects.group import Group
    from ocsf.v1_5_0.objects.job import Job
    from ocsf.v1_5_0.objects.kernel import Kernel
    from ocsf.v1_5_0.objects.module import Module
    from ocsf.v1_5_0.objects.network_connection_info import NetworkConnectionInfo
    from ocsf.v1_5_0.objects.network_interface import NetworkInterface
    from ocsf.v1_5_0.objects.peripheral_device import PeripheralDevice
    from ocsf.v1_5_0.objects.process import Process
    from ocsf.v1_5_0.objects.service import Service
    from ocsf.v1_5_0.objects.session import Session
    from ocsf.v1_5_0.objects.startup_item import StartupItem
    from ocsf.v1_5_0.objects.user import User


class QueryEvidence(OCSFBaseModel):
    """The specific resulting evidence information that was queried or discovered. When mapping raw telemetry data users should select the appropriate child object that best matches the evidence type as defined by query_type_id.

    See: https://schema.ocsf.io/1.5.0/objects/query_evidence
    """

    query_type_id: QueryTypeId = Field(
        ...,
        description="The normalized type of system query performed against a device or system component.",
    )
    connection_info: NetworkConnectionInfo | None = Field(
        default=None,
        description="The network connection information related to a Network Connection query type. [Recommended]",
    )
    file: File | None = Field(
        default=None,
        description="The file that is the target of the query when query_type_id indicates a File query. [Recommended]",
    )
    folder: File | None = Field(
        default=None,
        description="The folder that is the target of the query when query_type_id indicates a Folder query. [Recommended]",
    )
    group: Group | None = Field(
        default=None,
        description="The administrative group that is the target of the query when query_type_id indicates an Admin Group query. [Recommended]",
    )
    job: Job | None = Field(
        default=None,
        description="The job object that pertains to the event when query_type_id indicates a Job query. [Recommended]",
    )
    kernel: Kernel | None = Field(
        default=None,
        description="The kernel object that pertains to the event when query_type_id indicates a Kernel query. [Recommended]",
    )
    module: Module | None = Field(
        default=None,
        description="The module that pertains to the event when query_type_id indicates a Module query. [Recommended]",
    )
    network_interfaces: list[NetworkInterface] | None = Field(
        default=None,
        description="The physical or virtual network interfaces that are associated with the device when query_type_id indicates a Network Interfaces query. [Recommended]",
    )
    peripheral_device: PeripheralDevice | None = Field(
        default=None,
        description="The peripheral device that triggered the event when query_type_id indicates a Peripheral Device query. [Recommended]",
    )
    process: Process | None = Field(
        default=None,
        description="The process that pertains to the event when query_type_id indicates a Process query. [Recommended]",
    )
    query_type: str | None = Field(
        default=None,
        description="The normalized caption of query_type_id or the source-specific query type.",
    )
    service: Service | None = Field(
        default=None,
        description="The service that pertains to the event when query_type_id indicates a Service query. [Recommended]",
    )
    session: Session | None = Field(
        default=None,
        description="The authenticated user or service session when query_type_id indicates a Session query. [Recommended]",
    )
    startup_item: StartupItem | None = Field(
        default=None,
        description="The startup item object that pertains to the event when query_type_id indicates a Startup Item query. [Recommended]",
    )
    state: str | None = Field(
        default=None,
        description="The state of the socket, normalized to the caption of the state_id value. In the case of 'Other', it is defined by the event source.",
    )
    tcp_state_id: TcpStateId | None = Field(
        default=None, description="The state of the TCP socket for the network connection."
    )
    user: User | None = Field(
        default=None,
        description="The user that pertains to the event when query_type_id indicates a User query. [Recommended]",
    )
    users: list[User] | None = Field(
        default=None,
        description="The users that belong to the administrative group when query_type_id indicates a Users query.",
    )
