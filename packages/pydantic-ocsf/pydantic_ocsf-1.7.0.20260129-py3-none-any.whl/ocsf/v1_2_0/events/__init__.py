"""OCSF v1.2.0 event classes."""

from ocsf.v1_2_0.events.account_change import AccountChange
from ocsf.v1_2_0.events.admin_group_query import AdminGroupQuery
from ocsf.v1_2_0.events.api_activity import ApiActivity
from ocsf.v1_2_0.events.application_lifecycle import ApplicationLifecycle
from ocsf.v1_2_0.events.authentication import Authentication
from ocsf.v1_2_0.events.authorize_session import AuthorizeSession
from ocsf.v1_2_0.events.compliance_finding import ComplianceFinding
from ocsf.v1_2_0.events.config_state import ConfigState
from ocsf.v1_2_0.events.data_security_finding import DataSecurityFinding
from ocsf.v1_2_0.events.datastore_activity import DatastoreActivity
from ocsf.v1_2_0.events.detection_finding import DetectionFinding
from ocsf.v1_2_0.events.device_config_state_change import DeviceConfigStateChange
from ocsf.v1_2_0.events.dhcp_activity import DhcpActivity
from ocsf.v1_2_0.events.dns_activity import DnsActivity
from ocsf.v1_2_0.events.email_activity import EmailActivity
from ocsf.v1_2_0.events.email_file_activity import EmailFileActivity
from ocsf.v1_2_0.events.email_url_activity import EmailUrlActivity
from ocsf.v1_2_0.events.entity_management import EntityManagement
from ocsf.v1_2_0.events.file_activity import FileActivity
from ocsf.v1_2_0.events.file_hosting import FileHosting
from ocsf.v1_2_0.events.file_query import FileQuery
from ocsf.v1_2_0.events.folder_query import FolderQuery
from ocsf.v1_2_0.events.ftp_activity import FtpActivity
from ocsf.v1_2_0.events.group_management import GroupManagement
from ocsf.v1_2_0.events.http_activity import HttpActivity
from ocsf.v1_2_0.events.incident_finding import IncidentFinding
from ocsf.v1_2_0.events.inventory_info import InventoryInfo
from ocsf.v1_2_0.events.job_query import JobQuery
from ocsf.v1_2_0.events.kernel_activity import KernelActivity
from ocsf.v1_2_0.events.kernel_extension import KernelExtension
from ocsf.v1_2_0.events.kernel_object_query import KernelObjectQuery
from ocsf.v1_2_0.events.memory_activity import MemoryActivity
from ocsf.v1_2_0.events.module_activity import ModuleActivity
from ocsf.v1_2_0.events.module_query import ModuleQuery
from ocsf.v1_2_0.events.network_activity import NetworkActivity
from ocsf.v1_2_0.events.network_connection_query import NetworkConnectionQuery
from ocsf.v1_2_0.events.network_file_activity import NetworkFileActivity
from ocsf.v1_2_0.events.networks_query import NetworksQuery
from ocsf.v1_2_0.events.ntp_activity import NtpActivity
from ocsf.v1_2_0.events.patch_state import PatchState
from ocsf.v1_2_0.events.peripheral_device_query import PeripheralDeviceQuery
from ocsf.v1_2_0.events.process_activity import ProcessActivity
from ocsf.v1_2_0.events.process_query import ProcessQuery
from ocsf.v1_2_0.events.rdp_activity import RdpActivity
from ocsf.v1_2_0.events.scan_activity import ScanActivity
from ocsf.v1_2_0.events.scheduled_job_activity import ScheduledJobActivity
from ocsf.v1_2_0.events.security_finding import SecurityFinding
from ocsf.v1_2_0.events.service_query import ServiceQuery
from ocsf.v1_2_0.events.session_query import SessionQuery
from ocsf.v1_2_0.events.smb_activity import SmbActivity
from ocsf.v1_2_0.events.ssh_activity import SshActivity
from ocsf.v1_2_0.events.tunnel_activity import TunnelActivity
from ocsf.v1_2_0.events.user_access import UserAccess
from ocsf.v1_2_0.events.user_inventory import UserInventory
from ocsf.v1_2_0.events.user_query import UserQuery
from ocsf.v1_2_0.events.vulnerability_finding import VulnerabilityFinding
from ocsf.v1_2_0.events.web_resource_access_activity import WebResourceAccessActivity
from ocsf.v1_2_0.events.web_resources_activity import WebResourcesActivity

__all__ = [
    "AccountChange",
    "AdminGroupQuery",
    "ApiActivity",
    "ApplicationLifecycle",
    "Authentication",
    "AuthorizeSession",
    "ComplianceFinding",
    "ConfigState",
    "DataSecurityFinding",
    "DatastoreActivity",
    "DetectionFinding",
    "DeviceConfigStateChange",
    "DhcpActivity",
    "DnsActivity",
    "EmailActivity",
    "EmailFileActivity",
    "EmailUrlActivity",
    "EntityManagement",
    "FileActivity",
    "FileHosting",
    "FileQuery",
    "FolderQuery",
    "FtpActivity",
    "GroupManagement",
    "HttpActivity",
    "IncidentFinding",
    "InventoryInfo",
    "JobQuery",
    "KernelActivity",
    "KernelExtension",
    "KernelObjectQuery",
    "MemoryActivity",
    "ModuleActivity",
    "ModuleQuery",
    "NetworkActivity",
    "NetworkConnectionQuery",
    "NetworkFileActivity",
    "NetworksQuery",
    "NtpActivity",
    "PatchState",
    "PeripheralDeviceQuery",
    "ProcessActivity",
    "ProcessQuery",
    "RdpActivity",
    "ScanActivity",
    "ScheduledJobActivity",
    "SecurityFinding",
    "ServiceQuery",
    "SessionQuery",
    "SmbActivity",
    "SshActivity",
    "TunnelActivity",
    "UserAccess",
    "UserInventory",
    "UserQuery",
    "VulnerabilityFinding",
    "WebResourceAccessActivity",
    "WebResourcesActivity",
]
