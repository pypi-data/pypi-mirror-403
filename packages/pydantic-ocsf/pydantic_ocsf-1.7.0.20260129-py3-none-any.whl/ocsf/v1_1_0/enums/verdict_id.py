"""The normalized verdict of an Incident. enumeration."""

from enum import IntEnum


class VerdictId(IntEnum):
    """The normalized verdict of an Incident.

    See: https://schema.ocsf.io/1.1.0/data_types/verdict_id
    """

    VALUE_0 = 0  # The type is unknown.
    VALUE_1 = 1  # The incident is a false positive.
    VALUE_2 = 2  # The incident is a true positive.
    VALUE_3 = 3  # The incident can be disregarded as it is unimportant, an error or accident.
    VALUE_4 = 4  # The incident is suspicious.
    VALUE_5 = 5  # The incident is benign.
    VALUE_6 = 6  # The incident is a test.
    VALUE_7 = 7  # The incident has insufficient data to make a verdict.
    VALUE_8 = 8  # The incident is a security risk.
    VALUE_9 = 9  # The incident remediation or required actions are managed externally.
    VALUE_10 = 10  # The incident is a duplicate.
    VALUE_99 = 99  # The type is not mapped. See the <code>type</code> attribute, which contains a data source specific value.
