"""The normalized confidence refers to the accuracy of collected information related to the OSINT or how pertinent an indicator or analysis is to a specific event or finding. A low confidence means that the information collected or analysis conducted lacked detail or is not accurate enough to qualify an indicator as fully malicious. enumeration."""

from enum import IntEnum


class ConfidenceId(IntEnum):
    """The normalized confidence refers to the accuracy of collected information related to the OSINT or how pertinent an indicator or analysis is to a specific event or finding. A low confidence means that the information collected or analysis conducted lacked detail or is not accurate enough to qualify an indicator as fully malicious.

    See: https://schema.ocsf.io/1.5.0/data_types/confidence_id
    """

    VALUE_0 = 0  # The normalized confidence is unknown.
    VALUE_1 = 1  #
    VALUE_2 = 2  #
    VALUE_3 = 3  #
    VALUE_99 = 99  # The confidence is not mapped to the defined enum values. See the <code>confidence</code> attribute, which contains a data source specific value.
