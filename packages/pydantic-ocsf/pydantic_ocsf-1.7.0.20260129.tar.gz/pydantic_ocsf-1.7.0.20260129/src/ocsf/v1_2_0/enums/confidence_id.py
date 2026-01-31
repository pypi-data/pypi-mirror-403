"""The normalized confidence refers to the accuracy of the rule that created the finding. A rule with a low confidence means that the finding scope is wide and may create finding reports that may not be malicious in nature. enumeration."""

from enum import IntEnum


class ConfidenceId(IntEnum):
    """The normalized confidence refers to the accuracy of the rule that created the finding. A rule with a low confidence means that the finding scope is wide and may create finding reports that may not be malicious in nature.

    See: https://schema.ocsf.io/1.2.0/data_types/confidence_id
    """

    VALUE_0 = 0  # The normalized confidence is unknown.
    VALUE_1 = 1  #
    VALUE_2 = 2  #
    VALUE_3 = 3  #
    VALUE_99 = 99  # The confidence is not mapped to the defined enum values. See the <code>confidence</code> attribute, which contains a data source specific value.
