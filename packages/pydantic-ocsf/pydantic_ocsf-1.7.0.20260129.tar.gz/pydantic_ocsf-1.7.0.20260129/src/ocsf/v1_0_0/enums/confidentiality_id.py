"""The normalized identifier of the file content confidentiality indicator. enumeration."""

from enum import IntEnum


class ConfidentialityId(IntEnum):
    """The normalized identifier of the file content confidentiality indicator.

    See: https://schema.ocsf.io/1.0.0/data_types/confidentiality_id
    """

    VALUE_0 = 0  #
    VALUE_1 = 1  #
    VALUE_2 = 2  #
    VALUE_3 = 3  #
    VALUE_4 = 4  #
    VALUE_99 = 99  #
