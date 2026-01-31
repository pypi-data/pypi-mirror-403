"""OSINT object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.confidence_id import ConfidenceId
    from ocsf.v1_5_0.enums.detection_pattern_type_id import DetectionPatternTypeId
    from ocsf.v1_5_0.enums.severity_id import SeverityId
    from ocsf.v1_5_0.enums.tlp import Tlp
    from ocsf.v1_5_0.enums.type_id import TypeId
    from ocsf.v1_5_0.objects.analytic import Analytic
    from ocsf.v1_5_0.objects.attack import Attack
    from ocsf.v1_5_0.objects.autonomous_system import AutonomousSystem
    from ocsf.v1_5_0.objects.campaign import Campaign
    from ocsf.v1_5_0.objects.digital_signature import DigitalSignature
    from ocsf.v1_5_0.objects.dns_answer import DnsAnswer
    from ocsf.v1_5_0.objects.email import Email
    from ocsf.v1_5_0.objects.email_auth import EmailAuth
    from ocsf.v1_5_0.objects.file import File
    from ocsf.v1_5_0.objects.kill_chain_phase import KillChainPhase
    from ocsf.v1_5_0.objects.location import Location
    from ocsf.v1_5_0.objects.malware import Malware
    from ocsf.v1_5_0.objects.reputation import Reputation
    from ocsf.v1_5_0.objects.script import Script
    from ocsf.v1_5_0.objects.threat_actor import ThreatActor
    from ocsf.v1_5_0.objects.user import User
    from ocsf.v1_5_0.objects.vulnerability import Vulnerability
    from ocsf.v1_5_0.objects.whois import Whois


class Osint(OCSFBaseModel):
    """The OSINT (Open Source Intelligence) object contains details related to an indicator such as the indicator itself, related indicators, geolocation, registrar information, subdomains, analyst commentary, and other contextual information. This information can be used to further enrich a detection or finding by providing decisioning support to other analysts and engineers.

    See: https://schema.ocsf.io/1.5.0/objects/osint
    """

    type_id: TypeId = Field(..., description="The OSINT indicator type ID.")
    value: str = Field(
        ...,
        description="The actual indicator value in scope, e.g., a SHA-256 hash hexdigest or a domain name.",
    )
    answers: list[DnsAnswer] | None = Field(
        default=None,
        description="Any pertinent DNS answers information related to an indicator or OSINT analysis.",
    )
    attacks: list[Attack] | None = Field(
        default=None,
        description="MITRE ATT&CK Tactics, Techniques, and/or Procedures (TTPs) pertinent to an indicator or OSINT analysis.",
    )
    autonomous_system: AutonomousSystem | None = Field(
        default=None,
        description="Any pertinent autonomous system information related to an indicator or OSINT analysis.",
    )
    campaign: Campaign | None = Field(
        default=None,
        description="The campaign object describes details about the campaign that was the source of the activity.",
    )
    category: str | None = Field(
        default=None,
        description="Categorizes the threat indicator based on its functional or operational role.",
    )
    comment: str | None = Field(
        default=None,
        description="Analyst commentary or source commentary about an indicator or OSINT analysis.",
    )
    confidence: str | None = Field(
        default=None,
        description="The confidence of an indicator being malicious and/or pertinent, normalized to the caption of the confidence_id value. In the case of 'Other', it is defined by the event source or analyst.",
    )
    confidence_id: ConfidenceId | None = Field(
        default=None,
        description="The normalized confidence refers to the accuracy of collected information related to the OSINT or how pertinent an indicator or analysis is to a specific event or finding. A low confidence means that the information collected or analysis conducted lacked detail or is not accurate enough to qualify an indicator as fully malicious. [Recommended]",
    )
    created_time: int | None = Field(
        default=None,
        description="The timestamp when the indicator was initially created or identified.",
    )
    creator: User | None = Field(
        default=None,
        description="The identifier of the user, system, or organization that contributed the indicator.",
    )
    desc: str | None = Field(
        default=None,
        description="A detailed explanation of the indicator, including its context, purpose, and relevance.",
    )
    detection_pattern: str | None = Field(
        default=None,
        description="The specific detection pattern or signature associated with the indicator.",
    )
    detection_pattern_type: str | None = Field(
        default=None,
        description="The detection pattern type, normalized to the caption of the detection_pattern_type_id value. In the case of 'Other', it is defined by the event source.",
    )
    detection_pattern_type_id: DetectionPatternTypeId | None = Field(
        default=None,
        description="Specifies the type of detection pattern used to identify the associated threat indicator.",
    )
    email: Email | None = Field(
        default=None,
        description="Any email information pertinent to an indicator or OSINT analysis.",
    )
    email_auth: EmailAuth | None = Field(
        default=None,
        description="Any email authentication information pertinent to an indicator or OSINT analysis.",
    )
    expiration_time: int | None = Field(
        default=None,
        description="The expiration date of the indicator, after which it is no longer considered reliable.",
    )
    external_uid: str | None = Field(
        default=None,
        description="A unique identifier assigned by an external system for cross-referencing.",
    )
    file: File | None = Field(
        default=None,
        description="Any pertinent file information related to an indicator or OSINT analysis.",
    )
    intrusion_sets: list[str] | None = Field(
        default=None,
        description="A grouping of adversarial behaviors and resources believed to be associated with specific threat actors or campaigns. Intrusion sets often encompass multiple campaigns and are used to organize related activities under a common label.",
    )
    kill_chain: list[KillChainPhase] | None = Field(
        default=None,
        description="Lockheed Martin Kill Chain Phases pertinent to an indicator or OSINT analysis.",
    )
    labels: list[str] | None = Field(
        default=None,
        description="Tags or keywords associated with the indicator to enhance searchability.",
    )
    location: Location | None = Field(
        default=None,
        description="Any pertinent geolocation information related to an indicator or OSINT analysis.",
    )
    malware: list[Malware] | None = Field(
        default=None,
        description="A list of Malware objects, describing details about the identified malware.",
    )
    modified_time: int | None = Field(
        default=None,
        description="The timestamp of the last modification or update to the indicator.",
    )
    name: str | None = Field(
        default=None,
        description="The <code>name</code> is a pointer/reference to an attribute within the OCSF event data. For example: file.name.",
    )
    references: list[str] | None = Field(
        default=None,
        description="Provides a reference to an external source of information related to the CTI being represented. This may include a URL, a document, or some other type of reference that provides additional context or information about the CTI.",
    )
    related_analytics: list[Analytic] | None = Field(
        default=None, description="Any analytics related to an indicator or OSINT analysis."
    )
    reputation: Reputation | None = Field(
        default=None,
        description="Related reputational analysis from third-party engines and analysts for a given indicator or OSINT analysis.",
    )
    risk_score: int | None = Field(
        default=None, description="A numerical representation of the threat indicator’s risk level."
    )
    script: Script | None = Field(
        default=None,
        description="Any pertinent script information related to an indicator or OSINT analysis.",
    )
    severity: str | None = Field(
        default=None,
        description="Represents the severity level of the threat indicator, typically reflecting its potential impact or damage.",
    )
    severity_id: SeverityId | None = Field(
        default=None,
        description="The normalized severity level of the threat indicator, typically reflecting its potential impact or damage.",
    )
    signatures: list[DigitalSignature] | None = Field(
        default=None,
        description="Any digital signatures or hashes related to an indicator or OSINT analysis.",
    )
    src_url: Any | None = Field(
        default=None,
        description="The source URL of an indicator or OSINT analysis, e.g., a URL back to a TIP, report, or otherwise.",
    )
    subdomains: list[str] | None = Field(
        default=None,
        description="Any pertinent subdomain information - such as those generated by a Domain Generation Algorithm - related to an indicator or OSINT analysis.",
    )
    subnet: Any | None = Field(
        default=None,
        description="A CIDR or network block related to an indicator or OSINT analysis.",
    )
    threat_actor: ThreatActor | None = Field(
        default=None,
        description="A threat actor is an individual or group that conducts malicious cyber activities, often with financial, political, or ideological motives.",
    )
    tlp: Tlp | None = Field(
        default=None,
        description="The <a target='_blank' href='https://www.first.org/tlp/'>Traffic Light Protocol</a> was created to facilitate greater sharing of potentially sensitive information and more effective collaboration. TLP provides a simple and intuitive schema for indicating with whom potentially sensitive information can be shared. [Recommended]",
    )
    type_: str | None = Field(default=None, description="The OSINT indicator type.")
    uid: str | None = Field(default=None, description="The unique identifier for the OSINT object.")
    uploaded_time: int | None = Field(
        default=None,
        description="The timestamp indicating when the associated indicator or intelligence was added to the system or repository.",
    )
    vendor_name: str | None = Field(
        default=None,
        description="The vendor name of a tool which generates intelligence or provides indicators.",
    )
    vulnerabilities: list[Vulnerability] | None = Field(
        default=None, description="Any vulnerabilities related to an indicator or OSINT analysis."
    )
    whois: Whois | None = Field(
        default=None,
        description="Any pertinent WHOIS information related to an indicator or OSINT analysis.",
    )
