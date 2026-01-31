"""The normalized verdict (or status) ID of the evidence associated with the security detection. For example, Microsoft Graph Security Alerts contain a <code>verdict</code> enumeration for each type of <code>evidence</code> associated with the Alert. This is typically set by an automated investigation process or an analyst/investigator assigned to the finding. enumeration."""

from enum import IntEnum


class VerdictId(IntEnum):
    """The normalized verdict (or status) ID of the evidence associated with the security detection. For example, Microsoft Graph Security Alerts contain a <code>verdict</code> enumeration for each type of <code>evidence</code> associated with the Alert. This is typically set by an automated investigation process or an analyst/investigator assigned to the finding.

    See: https://schema.ocsf.io/1.7.0/data_types/verdict_id
    """

    VALUE_0 = 0  # The type is unknown.
    VALUE_1 = 1  # The verdict for the evidence has been identified as a False Positive.
    VALUE_2 = 2  # The verdict for the evidence has been identified as a True Positive.
    VALUE_3 = 3  # The verdict for the evidence is that is should be Disregarded.
    VALUE_4 = (
        4  # The verdict for the evidence is that the behavior has been identified as Suspicious.
    )
    VALUE_5 = 5  # The verdict for the evidence is that the behavior has been identified as Benign.
    VALUE_6 = 6  # The evidence is part of a Test, or other sanctioned behavior(s).
    VALUE_7 = 7  # There is insufficient data to render a verdict on the evidence.
    VALUE_8 = 8  # The verdict for the evidence is that the behavior has been identified as a Security Risk.
    VALUE_9 = (
        9  # The verdict for the evidence is Managed Externally, such as in a case management tool.
    )
    VALUE_10 = 10  # This evidence duplicates existing evidence related to this finding.
    VALUE_99 = 99  # The type is not mapped. See the <code>type</code> attribute, which contains a data source specific value.
