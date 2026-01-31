"""The cyber kill chain phase identifier. enumeration."""

from enum import IntEnum


class PhaseId(IntEnum):
    """The cyber kill chain phase identifier.

    See: https://schema.ocsf.io/1.5.0/data_types/phase_id
    """

    VALUE_0 = 0  # The kill chain phase is unknown.
    VALUE_1 = 1  # The attackers pick a target and perform a detailed analysis, start collecting information (email addresses, conferences information, etc.) and evaluate the victim’s vulnerabilities to determine how to exploit them.
    VALUE_2 = 2  # The attackers develop a malware weapon and aim to exploit the discovered vulnerabilities.
    VALUE_3 = (
        3  # The intruders will use various tactics, such as phishing, infected USB drives, etc.
    )
    VALUE_4 = (
        4  # The intruders start leveraging vulnerabilities to executed code on the victim’s system.
    )
    VALUE_5 = 5  # The intruders install malware on the victim’s system.
    VALUE_6 = 6  # Malware opens a command channel to enable the intruders to remotely manipulate the victim's system.
    VALUE_7 = 7  # With hands-on keyboard access, intruders accomplish the mission’s goal.
    VALUE_99 = 99  # The kill chain phase is not mapped. See the <code>phase</code> attribute, which contains a data source specific value.
