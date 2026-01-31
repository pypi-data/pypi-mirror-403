"""CVE object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_2_0.objects.cvss import Cvss
    from ocsf.v1_2_0.objects.cwe import Cwe
    from ocsf.v1_2_0.objects.epss import Epss
    from ocsf.v1_2_0.objects.product import Product


class Cve(OCSFBaseModel):
    """The Common Vulnerabilities and Exposures (CVE) object represents publicly disclosed cybersecurity vulnerabilities defined in CVE Program catalog (<a target='_blank' href='https://cve.mitre.org/'>CVE</a>). There is one CVE Record for each vulnerability in the catalog.

    See: https://schema.ocsf.io/1.2.0/objects/cve
    """

    uid: str = Field(
        ...,
        description="The Common Vulnerabilities and Exposures unique number assigned to a specific computer vulnerability. A CVE Identifier begins with 4 digits representing the year followed by a sequence of digits that acts as a unique identifier. For example: <code>CVE-2021-12345</code>.",
    )
    created_time: int | None = Field(
        default=None,
        description="The Record Creation Date identifies when the CVE ID was issued to a CVE Numbering Authority (CNA) or the CVE Record was published on the CVE List. Note that the Record Creation Date does not necessarily indicate when this vulnerability was discovered, shared with the affected vendor, publicly disclosed, or updated in CVE. [Recommended]",
    )
    cvss: list[Cvss] | None = Field(
        default=None,
        description="The CVSS object details Common Vulnerability Scoring System (<a target='_blank' href='https://www.first.org/cvss/'>CVSS</a>) scores from the advisory that are related to the vulnerability. [Recommended]",
    )
    cwe: Cwe | None = Field(
        default=None,
        description="The CWE object represents a weakness in a software system that can be exploited by a threat actor to perform an attack. The CWE object is based on the <a target='_blank' href='https://cwe.mitre.org/'>Common Weakness Enumeration (CWE)</a> catalog.",
    )
    cwe_uid: str | None = Field(
        default=None,
        description="The <a target='_blank' href='https://cwe.mitre.org/'>Common Weakness Enumeration (CWE)</a> unique identifier. For example: <code>CWE-787</code>.",
    )
    cwe_url: Any | None = Field(
        default=None,
        description="Common Weakness Enumeration (CWE) definition URL. For example: <code>https://cwe.mitre.org/data/definitions/787.html</code>.",
    )
    desc: str | None = Field(default=None, description="A brief description of the CVE Record.")
    epss: Epss | None = Field(
        default=None,
        description="The Exploit Prediction Scoring System (EPSS) object describes the estimated probability a vulnerability will be exploited. EPSS is a community-driven effort to combine descriptive information about vulnerabilities (CVEs) with evidence of actual exploitation in-the-wild. (<a target='_blank' href='https://www.first.org/epss/'>EPSS</a>).",
    )
    modified_time: int | None = Field(
        default=None,
        description="The Record Modified Date identifies when the CVE record was last updated.",
    )
    product: Product | None = Field(
        default=None, description="The product where the vulnerability was discovered."
    )
    references: list[str] | None = Field(
        default=None,
        description="A list of reference URLs with additional information about the CVE Record. [Recommended]",
    )
    title: str | None = Field(
        default=None,
        description="A title or a brief phrase summarizing the CVE record. [Recommended]",
    )
    type_: str | None = Field(
        default=None,
        description="<p>The vulnerability type as selected from a large dropdown menu during CVE refinement.</p>Most frequently used vulnerability types are: <code>DoS</code>, <code>Code Execution</code>, <code>Overflow</code>, <code>Memory Corruption</code>, <code>Sql Injection</code>, <code>XSS</code>, <code>Directory Traversal</code>, <code>Http Response Splitting</code>, <code>Bypass something</code>, <code>Gain Information</code>, <code>Gain Privileges</code>, <code>CSRF</code>, <code>File Inclusion</code>. For more information see <a target='_blank' href='https://www.cvedetails.com/vulnerabilities-by-types.php'>Vulnerabilities By Type</a> distributions. [Recommended]",
    )
